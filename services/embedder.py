import logging
from typing import List
from sentence_transformers import SentenceTransformer

# Set up some basic logging so we know what's happening behind the scenes
logger = logging.getLogger(__name__)

class TextEmbedder:
    """
    A simple helper class to handle converting our regular text into vector embeddings.
    We're defaulting to 'all-MiniLM-L6-v2' because it strikes a great balance 
    between speed and performance for everyday text tasks.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        logger.info(f"Waking up the embedding model '{model_name}'. This might take a few seconds...")
        # Load the model once when the class is created so we don't slow things down later
        self.model = SentenceTransformer(model_name)
        logger.info("Model is awake and ready to go!")

    def turn_chunks_into_embeddings(self, text_chunks: List[str]) -> List[List[float]]:
        """
        Takes a list of text pieces (chunks) and turns them into number lists (embeddings).
        
        Args:
            text_chunks: A list of strings. These are usually the pieces of documents you want to embed.
            
        Returns:
            A list of embeddings. Each embedding is a list of floating-point numbers.
        """
        # Let's handle the empty case gracefully
        if not text_chunks:
            logger.warning("Whoops, looks like you passed an empty list of chunks. Returning an empty list.")
            return []

        logger.info(f"Crunching the numbers: converting {len(text_chunks)} text chunks into embeddings...")
        
        # We use convert_to_numpy=True (the default) to get standard numpy arrays.
        # Then, we'll convert them into plain Python lists to make them easy to save or pass around.
        raw_embeddings = self.model.encode(text_chunks)
        
        # Convert each numpy array to a standard python list
        friendly_embeddings = [embedding.tolist() for embedding in raw_embeddings]
        
        logger.info("All done! Your embeddings are ready.")
        return friendly_embeddings

# A quick, easy-to-use function if you just want a one-liner
def generate_embeddings_for_chunks(text_chunks: List[str]) -> List[List[float]]:
    """
    A handy shortcut function to generate embeddings for a list of text chunks.
    Keep in mind: this loads the model every time you call it. 
    If you're doing this often, you're better off creating a TextEmbedder object!
    """
    embedder = TextEmbedder()
    return embedder.turn_chunks_into_embeddings(text_chunks)
