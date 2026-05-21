from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List

class DocumentChunker:
    """
    A simple utility class to break down large texts into smaller, manageable chunks.
    This helps when feeding documents into vector databases or LLMs
    where context windows are limited.
    """
    
    def __init__(self, chunk_size: int = 1000, overlap_size: int = 200):
        # We use a recursive character splitter because it tries to keep paragraphs
        # and sentences together as much as possible before splitting words.
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap_size,
            length_function=len,
            is_separator_regex=False,
            # We prioritize breaking text at natural boundaries like paragraphs and newlines
            separators=["\n\n", "\n", " ", ""]
        )

    def split_text_into_chunks(self, text_content: str) -> List[str]:
        """
        Takes a long string of text and splits it into a list of smaller strings (chunks).
        """
        if not text_content or not text_content.strip():
            return []
            
        chunks = self._text_splitter.split_text(text_content)
        return chunks

    def process_multiple_documents(self, documents: List[str]) -> List[str]:
        """
        Convenience method for when you have multiple separate documents to chunk at once.
        It simply gathers all chunks into a single flat list.
        """
        all_chunks = []
        for doc_text in documents:
            doc_chunks = self.split_text_into_chunks(doc_text)
            all_chunks.extend(doc_chunks)
            
        return all_chunks

# A quick helper function so you don't always have to instantiate the class
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Quickly chunk a single text string with default or custom sizes."""
    chunker = DocumentChunker(chunk_size=chunk_size, overlap_size=overlap)
    return chunker.split_text_into_chunks(text)
