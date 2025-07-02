import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"
    DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///instance/aipackager.db"
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "instance/uploads"
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 209715200))
    AI_MODEL = os.environ.get(
        "AI_MODEL", "gpt-4o-mini"
    )  # Default to gpt-4o-mini if not set


class ProductionConfig(Config):
    """Production specific configuration."""

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development specific configuration."""

    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing specific configuration."""

    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
