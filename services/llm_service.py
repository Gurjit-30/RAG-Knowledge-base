import os
from typing import List, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from services.vector_store import VectorDatabase
from services.embedder import TextEmbedder

class CustomVectorRetriever(BaseRetriever):
    """
    A custom retriever that connects our VectorDatabase and TextEmbedder
    to LangChain.
    """
    vector_db: Any
    embedder: Any
    top_k: int = 3
    threshold: float = 1.5
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Convert the query to an embedding, search the vector DB, and return LangChain Documents.
        """
        # 1. Embed the query
        query_embedding = self.embedder.turn_chunks_into_embeddings([query])[0]
        
        # 2. Search FAISS
        results = self.vector_db.search_similar(
            query_embedding, 
            number_of_results=self.top_k, 
            threshold=self.threshold
        )
        
        # 3. Convert results back to LangChain Document objects
        documents = []
        for res in results:
            text = res.get("text", "")
            # Remove text from metadata so it's not duplicated
            metadata = {k: v for k, v in res.items() if k != "text"}
            doc = Document(page_content=text, metadata=metadata)
            documents.append(doc)
            
        return documents

class LLMService:
    """
    Handles all the AI stuff: talking to the LLM and managing chat history.
    """
    
    def __init__(self, vector_db: VectorDatabase, embedder: TextEmbedder):
        # We'll use Gemini 1.5 Flash as our core model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3
        )
        
        # Create our retriever
        self.retriever = CustomVectorRetriever(
            vector_db=vector_db, 
            embedder=embedder,
            top_k=3,
            threshold=1.5
        )
        
        # Store chat histories in memory (dictionary mapping session_id to ChatMessageHistory)
        self.store = {}
        
        self.qa_chain = self._build_chain()
        
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Fetch or create a chat history for a specific user session."""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def _build_chain(self):
        """
        Assemble the RetrievalQA chain.
        """
        # This is our Custom System Prompt
        system_prompt = (
            "You are a helpful and highly technical AI assistant. "
            "Use ONLY the following pieces of retrieved context to answer the question. "
            "If you don't know the answer or if the answer is not in the context, "
            "just say 'I don't know'. Do not try to make up an answer. "
            "Keep your answer concise and technical.\n\n"
            "Context:\n{context}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        
        # This chain combines the retrieved documents into the prompt
        document_chain = create_stuff_documents_chain(self.llm, prompt)
        
        # This chain handles the actual retrieval step before passing to the document chain
        retrieval_chain = create_retrieval_chain(self.retriever, document_chain)
        
        # Finally, we wrap it all up with a history manager to remember past messages
        chain_with_history = RunnableWithMessageHistory(
            retrieval_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        
        return chain_with_history
        
    def ask_question(self, query: str, session_id: str = "default") -> dict:
        """
        Ask the AI a question, using the RAG pipeline.
        Returns the answer and the sources used.
        """
        # Run the chain!
        try:
            response = self.qa_chain.invoke(
                {"input": query},
                config={"configurable": {"session_id": session_id}}
            )
        except Exception as api_err:
            # Check for common API connectivity or quota errors (e.g., 503, 429)
            err_msg = str(api_err).lower()
            if "503" in err_msg or "unavailable" in err_msg:
                raise Exception("LLM_API_UNAVAILABLE: The AI service is currently down or unreachable (503). Please try again later.")
            elif "429" in err_msg or "quota" in err_msg:
                raise Exception("LLM_API_QUOTA: The AI service quota has been exceeded (429).")
            else:
                # Re-raise generic errors
                raise api_err
        
        # Extract the answer
        answer = response.get("answer", "I don't know.")
        
        # Extract the metadata (sources)
        sources = []
        for doc in response.get("context", []):
            meta = doc.metadata
            filename = meta.get("filename", "Unknown")
            page_num = meta.get("page_number", "Unknown")
            
            # We don't want to add duplicate sources, so we'll check first
            source_entry = {"filename": filename, "page_number": page_num}
            if source_entry not in sources:
                sources.append(source_entry)
                
        return {
            "answer": answer,
            "sources": sources
        }

    async def ask_question_stream(self, query: str, session_id: str = "default"):
        """
        Stream the AI's response token by token, along with sources.
        Yields JSON strings that can be sent over Server-Sent Events (SSE).
        """
        # We use astream_events to get the streaming tokens
        # The chain might emit different types of events. We care about "on_chat_model_stream"
        # We also want to capture the retrieved context at the end or beginning.
        
        sources_yielded = False
        
        try:
            async for event in self.qa_chain.astream_events(
                {"input": query},
                config={"configurable": {"session_id": session_id}},
                version="v1"
            ):
                kind = event["event"]
                
                # Intercept the retriever output to extract sources
                if kind == "on_retriever_end":
                    docs = event["data"].get("output", [])
                    if docs and not sources_yielded:
                        sources = []
                        for doc in docs:
                            meta = doc.metadata
                            source_entry = {
                                "filename": meta.get("filename", "Unknown"),
                                "page_number": meta.get("page_number", "Unknown")
                            }
                            if source_entry not in sources:
                                sources.append(source_entry)
                        
                        import json
                        yield json.dumps({"type": "sources", "data": sources}) + "\n"
                        sources_yielded = True

                # Intercept the LLM token stream
                elif kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        import json
                        yield json.dumps({"type": "token", "data": chunk.content}) + "\n"
                        
        except Exception as api_err:
            import json
            err_msg = str(api_err).lower()
            if "503" in err_msg or "unavailable" in err_msg:
                yield json.dumps({"type": "error", "data": "LLM_API_UNAVAILABLE: The AI service is currently down."}) + "\n"
            elif "429" in err_msg or "quota" in err_msg:
                yield json.dumps({"type": "error", "data": "LLM_API_QUOTA: The AI service quota has been exceeded."}) + "\n"
            else:
                yield json.dumps({"type": "error", "data": f"Error generating answer: {str(api_err)}"}) + "\n"

