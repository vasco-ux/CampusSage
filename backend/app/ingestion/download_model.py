import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.config import settings
from sentence_transformers import SentenceTransformer

def download_and_save():
    print("Saving all-MiniLM-L6-v2 directly into workspace:", settings.MODELS_DIR)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    save_path = os.path.join(settings.MODELS_DIR, "all-MiniLM-L6-v2")
    model.save(save_path)
    print("Successfully saved model directly to:", save_path)

if __name__ == "__main__":
    download_and_save()
