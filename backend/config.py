"""Database and application configuration."""
import os
from pathlib import Path

# Database
DB_PATH = Path(__file__).parent.parent / "data" / "querylens.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

# LLM (Google Gemini)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
ALLOW_CLIENT_LLM_CONFIG = os.getenv("ALLOW_CLIENT_LLM_CONFIG", "false").lower() == "true"

# CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
