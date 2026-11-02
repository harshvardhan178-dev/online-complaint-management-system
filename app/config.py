
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local environment variables.
# Hosting providers such as Render supply their own environment variables.
load_dotenv(BASE_DIR / ".env")


class Config:

    # Environment & Debug
    FLASK_ENV = os.getenv("FLASK_ENV", "development").strip().lower()

    # Never enable debug mode in production.
    if FLASK_ENV == "production":
        DEBUG = False
    else:
        DEBUG = os.getenv(
            "DEBUG",
            os.getenv("FLASK_DEBUG", "1")
        ).strip().lower() in ("true", "1", "yes")

    # Secret Key
    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not configured. "
            "Set it in your environment variables."
        )

    # Database Configuration
    raw_db_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("INTERNAL_DATABASE_URL")
        or f"sqlite:///{BASE_DIR / 'smartcomplaint.db'}"
    )

    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )
    elif raw_db_url.startswith("postgresql://"):
        raw_db_url = raw_db_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )

    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Session Management
    from cachelib.file import FileSystemCache
    SESSION_TYPE = "cachelib"
    SESSION_CACHELIB = FileSystemCache(cache_dir=str(BASE_DIR / ".flask_session"), threshold=1000)
    SESSION_PERMANENT = False
    SESSION_FILE_DIR = str(BASE_DIR / ".flask_session")

    # File Uploads
    upload_path = Path(os.getenv("UPLOAD_FOLDER", "uploads"))

    if not upload_path.is_absolute():
        upload_path = BASE_DIR / upload_path

    UPLOAD_FOLDER = str(upload_path)

    MAX_CONTENT_LENGTH = int(
        os.getenv("MAX_CONTENT_LENGTH", 50 * 1024 * 1024)
    )

    ALLOWED_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif",
        "pdf", "doc", "docx", "txt",
        "mp4", "mov", "avi", "mkv", "webm"
    }

    ALLOWED_VIDEO_EXTENSIONS = {
        "mp4", "mov", "avi", "mkv", "webm"
    }

    # Mail Configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))

    MAIL_USE_TLS = os.getenv(
        "MAIL_USE_TLS", "true"
    ).strip().lower() in ("true", "1", "yes")

    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")

    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        "noreply@smartcomplaint.com"
    )

    # Default Administrator Configuration
    DEFAULT_ADMIN_EMAIL = os.getenv(
        "DEFAULT_ADMIN_EMAIL",
        "admin@smartcomplaint.com"
    )

    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD")

    DEFAULT_ADMIN_NAME = os.getenv(
        "DEFAULT_ADMIN_NAME",
        "System Administrator"
    )
