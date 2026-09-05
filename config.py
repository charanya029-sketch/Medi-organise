import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

IS_VERCEL = bool(os.environ.get("VERCEL"))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "medical-records-dev-key-change-in-prod-2026")
    
    # SQLite / Database path: use /tmp on Vercel if DATABASE_URL is not explicitly configured
    if IS_VERCEL and "DATABASE_URL" not in os.environ:
        SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/database.db"
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'database.db'}"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads: use /tmp/uploads on Vercel serverless functions
    if IS_VERCEL:
        UPLOAD_FOLDER = Path("/tmp/uploads")
    else:
        UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 16)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
    
    # AI / LLM Configuration
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
    OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Tesseract OCR Path (Auto-detected if empty)
    TESSERACT_PATH = os.environ.get("TESSERACT_PATH", "")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
