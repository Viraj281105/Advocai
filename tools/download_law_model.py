# tools/download_law_model.py
from sentence_transformers import SentenceTransformer
import os

print("Downloading model... (~90MB, much faster)")

model = SentenceTransformer("all-MiniLM-L6-v2")

save_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "local-embedder")
os.makedirs(save_path, exist_ok=True)

model.save(save_path)
print(f"Model saved to: {save_path}")

# Quick test
test = model.encode(["This is a legal contract clause"])
print(f"Test embedding shape: {test.shape}")
print("Done!")