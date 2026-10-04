"""
Magnus Dynamic CMS - Main Entrypoint
Run with: python app.py
"""
import os
import sys

# Ensure root is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
    print(f"==================================================")
    print(f" Starting Magnus Dynamic CMS Server")
    print(f" URL:             http://127.0.0.1:{port}/")
    print(f" Login Page:      http://127.0.0.1:{port}/login")
    print(f" Magnus Home:     http://127.0.0.1:{port}/home")
    print(f"==================================================")
    app.run(host="127.0.0.1", port=port, debug=debug)
