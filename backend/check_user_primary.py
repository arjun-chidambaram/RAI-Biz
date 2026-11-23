import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.models import User, Business, BusinessUser, AIApplication, Dataset
from app.services.auth_service import get_user_primary_business, get_user_primary_application

engine = create_engine("sqlite:///./rai_biz.db", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

user = db.query(User).filter(User.email == "arjunchidambaram.b@gmail.com").first()
if user:
    primary_biz = get_user_primary_business(db, user.id)
    primary_app = get_user_primary_application(db, user.id)
    print(f"User: {user.email}")
    print(f"Primary Biz: ID={primary_biz.id if primary_biz else None}, Name='{primary_biz.name if primary_biz else None}'")
    print(f"Primary App: ID={primary_app.id if primary_app else None}, Name='{primary_app.name if primary_app else None}'")
else:
    print("User not found")

db.close()
