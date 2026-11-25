import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

# Explicitly load .env and .env.txt from backend directory and project root directory
for env_candidate in [
    BASE_DIR / ".env",
    BASE_DIR / ".env.txt",
    BASE_DIR.parent / ".env",
    BASE_DIR.parent / ".env.txt",
]:
    if env_candidate.exists():
        load_dotenv(env_candidate, override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "RAI-Biz Governance Platform"
    API_V1_STR: str = "/api"
    BASE_DIR: Path = BASE_DIR
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'rai_biz.db'}")
    
    # Customer Backup Database (Supabase) - Decoupled from Primary Neon Engine
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_DATABASE_URL: str = os.getenv("SUPABASE_DATABASE_URL", "")
    
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    DATA_DIR: Path = BASE_DIR / "app" / "data"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    @property
    def normalized_database_url(self) -> str:
        url = self.DATABASE_URL.strip()
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return url
    
    # Auth & Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "rai-biz-secret-key-super-secure-production-ready-2026")
    SESSION_COOKIE_NAME: str = "rai_biz_session"
    CSRF_COOKIE_NAME: str = "rai_biz_csrf"
    SESSION_MAX_AGE_DAYS: int = 7
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Resend Email Configuration
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "RAI-Biz <onboarding@resend.dev>")
    
    # SMTP Fallback Configuration (Gmail SMTP)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    class Config:
        env_file = (
            str(BASE_DIR / ".env"),
            str(BASE_DIR / ".env.txt"),
            str(BASE_DIR.parent / ".env"),
            str(BASE_DIR.parent / ".env.txt"),
        )
        extra = "ignore"
        case_sensitive = True

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
