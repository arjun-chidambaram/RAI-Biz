import os
import sys
import hashlib
import random
import datetime
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.models import Dataset, DatasetRecord, IngestionLog, AIApplication, Business
from app.config import settings

def generate_suntech_automotive_dataset(n_samples: int = 250) -> pd.DataFrame:
    np.random.seed(101)
    random.seed(101)

    booking_ids = [f"BK-{2000 + i + 1}" for i in range(n_samples)]
    genders = np.random.choice(["Male", "Female"], size=n_samples, p=[0.53, 0.47])
    age_groups = np.random.choice(["18-25", "26-40", "41-60", "60+"], size=n_samples, p=[0.18, 0.48, 0.26, 0.08])
    vehicle_types = np.random.choice(["Sedan", "SUV", "Hatchback", "Luxury Sports", "Truck / Van"], size=n_samples, p=[0.32, 0.35, 0.18, 0.10, 0.05])
    vehicle_ages = np.clip(np.random.normal(4.2, 2.5, size=n_samples), 0.5, 12.0).round(1)
    paint_condition = np.clip(np.random.normal(68.0, 16.0, size=n_samples), 20.0, 99.0).round(1)
    service_packages = np.random.choice([
        "Express Wash & Wax",
        "Interior Steam Clean",
        "2-Step Paint Correction",
        "Ceramic Coating Elite",
        "Graphene Shield Pro"
    ], size=n_samples, p=[0.25, 0.22, 0.28, 0.15, 0.10])
    
    quote_base = {
        "Express Wash & Wax": 2200,
        "Interior Steam Clean": 4500,
        "2-Step Paint Correction": 9500,
        "Ceramic Coating Elite": 18500,
        "Graphene Shield Pro": 26000
    }
    quotes = [int(quote_base[pkg] + np.random.normal(0, quote_base[pkg] * 0.08)) for pkg in service_packages]
    lead_times = np.clip(np.random.geometric(p=0.35, size=n_samples), 1, 14)

    # Acceptance probability modeled on service demand and vehicle age
    approved = []
    for g, v_type, v_age, p_cond, pkg, q in zip(genders, vehicle_types, vehicle_ages, paint_condition, service_packages, quotes):
        # Slightly higher acceptance for newer vehicles and professional packages
        propensity = 0.55
        if v_age <= 3.0 and pkg in ["Ceramic Coating Elite", "Graphene Shield Pro"]:
            propensity += 0.25
        elif p_cond < 50.0 and pkg == "2-Step Paint Correction":
            propensity += 0.20
        elif q > 22000 and v_age > 7.0:
            propensity -= 0.30
        
        # Ensure parity evaluation can observe realistic demographic variations
        if g == "Female" and pkg in ["2-Step Paint Correction", "Ceramic Coating Elite"]:
            # Slight quote friction simulation for audit detection
            propensity -= 0.08
            
        is_app = 1 if (propensity + np.random.normal(0, 0.15)) >= 0.50 else 0
        approved.append(is_app)

    # Synthetic PII for Privacy Guard evaluation
    first_names_m = ["Aarav", "Rohan", "Vikram", "Aditya", "Rahul", "Karthik", "Siddharth", "Arjun", "Dev", "Manish"]
    first_names_f = ["Ananya", "Pooja", "Priya", "Sneha", "Kavita", "Ritu", "Deepika", "Neha", "Shreya", "Meera"]
    last_names = ["Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Choudhury", "Gupta", "Rao", "Menon"]

    phones = []
    emails = []
    for i, g in enumerate(genders):
        fn = random.choice(first_names_f if g == "Female" else first_names_m)
        ln = random.choice(last_names)
        ph = f"+91-98{random.randint(10000000, 99999999)}"
        em = f"{fn.lower()}.{ln.lower()}{random.randint(10, 99)}@suntech-demo.in"
        phones.append(ph)
        emails.append(em)

    df = pd.DataFrame({
        "booking_id": booking_ids,
        "customer_gender": genders,
        "customer_age_group": age_groups,
        "vehicle_type": vehicle_types,
        "vehicle_age_years": vehicle_ages,
        "paint_condition_score": paint_condition,
        "service_package": service_packages,
        "quote_amount_inr": quotes,
        "lead_time_days": lead_times,
        "service_approved": approved,
        "phone": phones,
        "email": emails
    })

    return df

def seed_suntech_dataset_in_db():
    engine = create_engine("sqlite:///./rai_biz.db", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    db = Session()

    # Find Suntech applications
    apps = db.query(AIApplication).filter(AIApplication.name.like("%Car Detailing%")).all()
    if not apps:
        print("Error: No Smart Car Detailing Assistant application found!")
        db.close()
        return

    print(f"Found {len(apps)} automotive detailing applications:")
    for a in apps:
        print(f"  App ID {a.id} (Biz ID {a.business_id}): '{a.name}'")

    # Generate synthetic CSV
    df = generate_suntech_automotive_dataset(250)
    filename = "suntech_car_detailing_dataset.csv"
    upload_path = settings.UPLOAD_DIR / filename
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(upload_path, index=False)
    print(f"\nSaved synthetic dataset to: {upload_path} ({len(df)} records, {len(df.columns)} columns)")

    file_bytes = upload_path.read_bytes()
    checksum = hashlib.sha256(file_bytes).hexdigest()

    # Register for each Suntech application that doesn't have it yet
    for a in apps:
        existing = db.query(Dataset).filter(Dataset.application_id == a.id, Dataset.filename == filename).first()
        if not existing:
            ds = Dataset(
                application_id=a.id,
                filename=filename,
                original_filename=filename,
                file_path=str(upload_path),
                file_size_bytes=len(file_bytes),
                row_count=len(df),
                column_count=len(df.columns),
                checksum=checksum,
                schema_version="1.0-automotive",
                status="Active"
            )
            db.add(ds)
            db.flush()

            # Add sample records
            for idx, row in df.head(50).iterrows():
                rec = DatasetRecord(
                    dataset_id=ds.id,
                    row_index=idx,
                    record_type="clean",
                    raw_data_json=row.to_json()
                )
                db.add(rec)

            log = IngestionLog(
                dataset_id=ds.id,
                event_type="IngestionSuccess",
                details_json=f'{{"message": "Synthetic automotive detailing dataset successfully ingested with {len(df)} rows and {len(df.columns)} columns."}}'
            )
            db.add(log)
            print(f"  -> Registered Dataset ID {ds.id} for Application ID {a.id} ('{a.name}')")
        else:
            print(f"  -> Dataset already exists (ID {existing.id}) for Application ID {a.id}")

    db.commit()
    db.close()
    print("Database registration complete.")

if __name__ == "__main__":
    seed_suntech_dataset_in_db()
