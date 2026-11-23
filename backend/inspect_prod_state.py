import sys
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.models import (
    User, Business, BusinessUser, AIApplication, Assessment,
    Dataset, Risk, Recommendation, FairnessResult, PrivacyFinding
)

engine = create_engine("sqlite:///./rai_biz.db", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

print("=== USERS ===")
for u in db.query(User).all():
    print(f"ID: {u.id}, Email: {u.email}, Active: {u.is_active}, Verified: {u.is_verified}")

print("\n=== BUSINESSES ===")
for b in db.query(Business).all():
    members = db.query(BusinessUser).filter(BusinessUser.business_id == b.id).all()
    user_ids = [m.user_id for m in members]
    print(f"ID: {b.id}, Name: '{b.name}', Industry: '{b.industry}', Location: '{b.location}', UserIDs: {user_ids}")

print("\n=== AI APPLICATIONS ===")
for a in db.query(AIApplication).all():
    print(f"ID: {a.id}, BizID: {a.business_id}, Name: '{a.name}', Function: '{a.business_function}'")

print("\n=== DATASETS ===")
for d in db.query(Dataset).all():
    print(f"ID: {d.id}, AppID: {d.application_id}, File: '{d.filename}', Rows: {d.row_count}, Cols: {d.column_count}")

print("\n=== ASSESSMENTS ===")
for ass in db.query(Assessment).all():
    print(f"ID: {ass.id}, BizID: {ass.business_id}, AppID: {ass.application_id}, Name: '{ass.name}', Score: {ass.overall_score}%")

print("\n=== RISKS COUNT PER APP ===")
for a in db.query(AIApplication).all():
    risk_count = db.query(Risk).filter(Risk.application_id == a.id).count()
    print(f"App {a.id} ('{a.name}'): {risk_count} risks")

db.close()
