"""Test if model loads correctly."""
from sentence_transformers import SentenceTransformer
import os

model_path = "./data/models/paraphrase-multilingual-MiniLM-L12-v2"

print(f"Testing model from: {model_path}")
print(f"Model exists: {os.path.exists(model_path)}")
print(f"Files in model dir: {os.listdir(model_path)}")
print()

try:
    print("Loading model...")
    model = SentenceTransformer(model_path)
    print("✅ Model loaded successfully!")

    # Test encoding
    print("\nTesting encoding...")
    text = "Chung cư 2 tỷ Cầu Giấy"
    embedding = model.encode(text)
    print(f"✅ Encoded text: '{text}'")
    print(f"   Embedding shape: {embedding.shape}")
    print(f"   Embedding dim: {len(embedding)}")

    print("\n✅ Model is working! You can now enable VectorDB.")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nModel may be incomplete. Try downloading again or disable VectorDB.")
