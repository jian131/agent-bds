"""
Download sentence-transformers model quickly.
"""
from sentence_transformers import SentenceTransformer
import os

print("Downloading paraphrase-multilingual-MiniLM-L12-v2 (471MB)...")
print("This may take 5-10 minutes depending on your internet speed.")

# Create cache directory
cache_dir = "./data/models"
os.makedirs(cache_dir, exist_ok=True)

# Download model
model = SentenceTransformer(
    'paraphrase-multilingual-MiniLM-L12-v2',
    cache_folder=cache_dir
)

print(f"\n✅ Model downloaded successfully to: {cache_dir}")
print("You can now enable VectorDB in storage/vector_db.py")
