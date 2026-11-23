import sqlite3
from pathlib import Path
from .database import engine, Base
from .config import settings
from .models import User, Business, AIApplication, EmailOTP, SessionRecord, BusinessUser

def run_migration():
    print(f"Running safe auth migration on {settings.DATABASE_URL}...")
    
    # 1. Direct SQLite column checks for existing tables
    if settings.DATABASE_URL.startswith("sqlite"):
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if Path(db_path).exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check users table columns
            columns = [row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()]
            
            if "is_verified" not in columns:
                print("Adding 'is_verified' column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0")
                
            if "last_login" not in columns:
                print("Adding 'last_login' column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN last_login DATETIME")
                
            conn.commit()
            conn.close()

    # 2. Create any missing tables (email_otps, sessions, business_users)
    Base.metadata.create_all(bind=engine)
    print("Database tables verified/created successfully.")

if __name__ == "__main__":
    run_migration()
