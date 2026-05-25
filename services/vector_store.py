import faiss
import numpy as np
from typing import List, Dict, Any

class VectorDatabase:
    """
    Handles our connection to the FAISS vector database.
    This helps us store and search for similar documents quickly.
    """
    
    def __init__(self, embedding_dimension: int):
        """
        Set up the FAISS index based on how large our embeddings are.
        
        Args:
            embedding_dimension: The size of the vector embeddings (e.g. 1536 for OpenAI)
        """
        # We use an L2 distance flat index because it gives exact results 
        # and is simple to get started with.
        self.embedding_dimension = embedding_dimension
        self.index = faiss.IndexFlatL2(self.embedding_dimension)
        
    def add_embeddings(self, embeddings: List[List[float]]) -> None:
        """
        Save a batch of embeddings into our database.
        """
        if not embeddings:
            print("No embeddings provided to add.")
            return
            
        # FAISS expects our embeddings to be a float32 numpy array
        vectors_to_add = np.array(embeddings).astype('float32')
        self.index.add(vectors_to_add)
        
    def search_similar(self, query_embedding: List[float], number_of_results: int = 5) -> Dict[str, Any]:
        """
        Find the most similar embeddings to our query.
        """
        query_vector = np.array([query_embedding]).astype('float32')
        
        # This returns the distances and the IDs (indices) of the closest matches
        distances, match_indices = self.index.search(query_vector, number_of_results)
        
        return {
            "distances": distances[0].tolist(),
            "match_indices": match_indices[0].tolist()
        }
        
    def get_total_items(self) -> int:
        """
        Check how many vectors we currently have stored.
        """
        return self.index.ntotal
