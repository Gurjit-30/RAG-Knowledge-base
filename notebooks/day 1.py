from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')  # free, runs locally

sentences = [
    "The cat sat on the mat",
    "A kitten rested on a rug",       # should be close to sentence 1
    "Stock markets crashed today",    # should be far from sentence 1
]

embeddings = model.encode(sentences)

# Cosine similarity — 1.0 = identical, 0.0 = unrelated
def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

print(cosine_sim(embeddings[0], embeddings[1]))  # expect ~0.85 (similar)
print(cosine_sim(embeddings[0], embeddings[2]))  # expect ~0.05 (different)