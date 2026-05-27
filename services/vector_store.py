import faiss
import numpy as np
import json
import os
from typing import List, Dict, Any, Optional

class VectorDatabase:
    """
    Handles our connection to the FAISS vector database.
    This helps us store and search for similar documents quickly.
    """
    
    def __init__(self, embedding_dimension: int = 384, persist_dir: str = "data/vector_store"):
        """
        Set up the FAISS index based on how large our embeddings are.
        
        Args:
            embedding_dimension: The size of the vector embeddings.
            persist_dir: Where to save the index on disk.
        """
        self.embedding_dimension = embedding_dimension
        self.persist_dir = persist_dir
        self.index = faiss.IndexFlatL2(self.embedding_dimension)
        # Map chunk IDs (which match faiss index positions) to a dictionary containing text and metadata
        self.chunk_map: Dict[int, Dict[str, Any]] = {}
        
    def add_embeddings(self, embeddings: List[List[float]], metadata_list: List[Dict[str, Any]]) -> None:
        """
        Save a batch of embeddings into our database, along with their text and metadata.
        """
        if not embeddings:
            print("No embeddings provided to add.")
            return
            
        vectors_to_add = np.array(embeddings).astype('float32')
        
        start_id = self.index.ntotal
        self.index.add(vectors_to_add)
        
        # Save the metadata into our map so we can retrieve the text later
        for i, meta in enumerate(metadata_list):
            self.chunk_map[start_id + i] = meta
            
    def search_similar(self, query_embedding: List[float], number_of_results: int = 3, threshold: float = 1.5) -> List[Dict[str, Any]]:
        """
        Find the most similar embeddings to our query, returning the actual text and metadata.
        Filters out matches that have a distance greater than the threshold (L2 distance: lower is better).
        """
        if self.index.ntotal == 0:
            return []
            
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search for the closest matches
        distances, match_indices = self.index.search(query_vector, number_of_results)
        
        results = []
        for dist, idx in zip(distances[0], match_indices[0]):
            if idx == -1: # FAISS returns -1 if not enough results
                continue
            
            # Since it's L2 distance, lower distance means higher similarity.
            # We use a threshold to filter out bad matches.
            if dist <= threshold:
                item_data = self.chunk_map.get(int(idx), {})
                # Add distance for debugging/inspection
                item_data_copy = item_data.copy()
                item_data_copy["similarity_distance"] = float(dist)
                results.append(item_data_copy)
                
        return results
        
    def get_total_items(self) -> int:
        """
        Check how many vectors we currently have stored.
        """
        return self.index.ntotal

    def save_to_disk(self) -> None:
        """
        Save the FAISS index and the chunk mapping to disk.
        """
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Save the FAISS index
        index_path = os.path.join(self.persist_dir, "faiss.index")
        faiss.write_index(self.index, index_path)
        
        # Save the mapping
        map_path = os.path.join(self.persist_dir, "chunk_map.json")
        with open(map_path, "w", encoding="utf-8") as f:
            # json needs string keys, so we convert the integer keys
            string_key_map = {str(k): v for k, v in self.chunk_map.items()}
            json.dump(string_key_map, f, ensure_ascii=False, indent=2)
            
    def load_from_disk(self) -> bool:
        """
        Reload the FAISS index and the chunk mapping from disk.
        Returns True if successful, False otherwise.
        """
        index_path = os.path.join(self.persist_dir, "faiss.index")
        map_path = os.path.join(self.persist_dir, "chunk_map.json")
        
        if os.path.exists(index_path) and os.path.exists(map_path):
            # Load the FAISS index
            self.index = faiss.read_index(index_path)
            
            # Load the mapping and convert keys back to integers
            with open(map_path, "r", encoding="utf-8") as f:
                string_key_map = json.load(f)
                self.chunk_map = {int(k): v for k, v in string_key_map.items()}
                
            return True
        return False
