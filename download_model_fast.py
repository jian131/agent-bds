"""
Download model with resume support and progress tracking.
"""
import os
import sys
from pathlib import Path

print("="*60)
print("DOWNLOADING PARAPHRASE-MULTILINGUAL-MINILM-L12-V2")
print("Size: 471MB | Time: 5-10 minutes")
print("="*60)

cache_dir = Path("./data/models/paraphrase-multilingual-MiniLM-L12-v2")
cache_dir.mkdir(parents=True, exist_ok=True)

print(f"\n📁 Target directory: {cache_dir.absolute()}")

# Method 1: Try huggingface_hub first (fastest with resume)
try:
    print("\n🚀 Method 1: Using huggingface_hub...")
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        local_dir=str(cache_dir),
        local_dir_use_symlinks=False,
        resume_download=True
    )
    print("\n✅ Download completed via huggingface_hub!")
    sys.exit(0)

except Exception as e:
    print(f"⚠️ Method 1 failed: {e}")
    print("\n🔄 Trying Method 2...")

# Method 2: Fallback to sentence_transformers
try:
    print("🚀 Method 2: Using sentence_transformers...")
    from sentence_transformers import SentenceTransformer

    # This will download to default cache and we can copy later
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("\n✅ Download completed via sentence_transformers!")
    print(f"📍 Model cached at: {model._model_card_text if hasattr(model, '_model_card_text') else 'default cache'}")

except Exception as e:
    print(f"\n❌ Both methods failed: {e}")
    print("\n💡 Manual download:")
    print("   1. Visit: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    print("   2. Download all files to:", cache_dir.absolute())
    sys.exit(1)
