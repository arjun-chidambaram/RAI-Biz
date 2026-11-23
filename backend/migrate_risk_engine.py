import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "rai_biz.db")

def run_migration():
    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Update 'risks' table
    cursor.execute("PRAGMA table_info(risks)")
    existing_risk_cols = [row[1] for row in cursor.fetchall()]

    new_risk_cols = [
        ("risk_key", "VARCHAR(100)"),
        ("category", "VARCHAR(50)"),
        ("likelihood", "VARCHAR(20) DEFAULT 'Medium'"),
        ("impact", "VARCHAR(20) DEFAULT 'Medium'"),
        ("exposure_factor", "VARCHAR(20) DEFAULT 'Medium'"),
        ("control_effectiveness", "VARCHAR(20) DEFAULT 'Weak'"),
        ("risk_score", "FLOAT DEFAULT 50.0"),
        ("evidence_source", "VARCHAR(100) DEFAULT 'Self-reported assessment answer'"),
        ("is_verified", "BOOLEAN DEFAULT 0"),
        ("lifecycle_status", "VARCHAR(50) DEFAULT 'New'"),
        ("responsible_owner", "VARCHAR(100)"),
        ("target_date", "VARCHAR(50)"),
        ("completion_notes", "TEXT"),
        ("supporting_evidence", "TEXT"),
        ("remediation_history_json", "TEXT")
    ]

    for col_name, col_type in new_risk_cols:
        if col_name not in existing_risk_cols:
            cursor.execute(f"ALTER TABLE risks ADD COLUMN {col_name} {col_type}")
            print(f"  Added column 'risks.{col_name}' ({col_type})")
        else:
            print(f"  Column 'risks.{col_name}' already exists.")

    # 2. Update 'ai_applications' table
    cursor.execute("PRAGMA table_info(ai_applications)")
    existing_app_cols = [row[1] for row in cursor.fetchall()]

    new_app_cols = [
        ("affected_stakeholders", "VARCHAR(255)"),
        ("external_services", "VARCHAR(255)"),
        ("infrastructure_type", "VARCHAR(100)")
    ]

    for col_name, col_type in new_app_cols:
        if col_name not in existing_app_cols:
            cursor.execute(f"ALTER TABLE ai_applications ADD COLUMN {col_name} {col_type}")
            print(f"  Added column 'ai_applications.{col_name}' ({col_type})")
        else:
            print(f"  Column 'ai_applications.{col_name}' already exists.")

    conn.commit()
    conn.close()
    print("Migration completed successfully with zero data loss!")

if __name__ == "__main__":
    run_migration()
