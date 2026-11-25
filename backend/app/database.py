from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

db_url = settings.normalized_database_url
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False
    )
elif db_url.startswith("postgresql"):
    # Neon Serverless PostgreSQL optimizations
    if "sslmode=" not in db_url.lower():
        connect_args["sslmode"] = "require"
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,  # Transparently reconnects when Neon compute wakes up
        pool_recycle=300,    # Recycle connections every 5 minutes
        pool_size=10,
        max_overflow=20,
        echo=False
    )
else:
    engine = create_engine(
        db_url,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
