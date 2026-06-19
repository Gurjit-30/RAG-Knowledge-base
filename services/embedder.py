import logging
import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)

class TextEmbedder:
    """
    A helper class to handle converting text into vector embeddings using the Google Gemini API.
    This saves massive amounts of memory compared to running a local PyTorch model!
    """
    
    def __init__(self, model_name: str = 'models/embedding-001'):
        logger.info(f"Connecting to Gemini API for embeddings using model '{model_name}'...")
        # Get the API key from environment
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY is missing! Embeddings will fail.")
            
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=api_key
        )
        logger.info("Gemini Embedding service is ready to go!")

    def turn_chunks_into_embeddings(self, text_chunks: List[str]) -> List[List[float]]:
        if not text_chunks:
            logger.warning("Empty list of chunks. Returning an empty list.")
            return []

        logger.info(f"Calling Gemini API to convert {len(text_chunks)} text chunks into embeddings...")
        
        # Use Langchain's embed_documents which handles batching automatically
        friendly_embeddings = self.embeddings.embed_documents(text_chunks)
        
        logger.info("All done! Your embeddings are ready.")
        return friendly_embeddings

def generate_embeddings_for_chunks(text_chunks: List[str]) -> List[List[float]]:
    embedder = TextEmbedder()
    return embedder.turn_chunks_into_embeddings(text_chunks)
