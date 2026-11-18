import os
import sys
import webbrowser
import uvicorn

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from app.database.connection import init_db

def main():
    print("=" * 70)
    print(" 🌐 Starting CampusSage: AI-Powered Web Information & Opportunity Hub")
    print("=" * 70)

    # Initialize SQLite schema
    init_db()

    print("\n[SERVER] CampusSage Web Application launching at http://127.0.0.1:8000")
    print("[SERVER] Press Ctrl+C in this terminal to stop the application.\n")

    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

    from app.main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
