from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    UPLOAD_DIR: str = "uploads"
    APP_NAME: str = "PDF Notes AI"
    DEBUG: bool = True
    GROQ_API_KEY: str = ""
    TESSERACT_PATH: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    class Config:
        env_file = ".env"

settings = Settings()

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)