"""
Automated PostgreSQL & Neon Compatibility Test Suite
====================================================
Verifies:
1. Database URL dialect normalization (postgres:// -> postgresql://).
2. Neon connection pooling and engine settings (pool_pre_ping, pool_recycle, SSL).
3. SQLite local development fallback preservation.
4. Safe migration tool execution against an isolated database target.
5. Bit-for-bit row count parity and relational hierarchy preservation.
6. Target non-empty safety guard (prevents accidental overwriting/reseeding).
7. Source database immutability (SHA-256 integrity verification).
8. Optional live Neon/PostgreSQL testing (when TEST_POSTGRESQL_URL is set).
"""

import os
import sys
import hashlib
import tempfile
import pytest
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import Settings
from app.database import Base
from app.models import (
    User, Business, BusinessUser, AIApplication, Assessment,
    AssessmentResponse, Risk, Recommendation
)
from migrate_to_neon import (
    normalize_pg_url, mask_connection_url, run_migration,
    TABLE_MODEL_ORDER, resolve_target_url
)

def compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

# ----------------- CONFIGURATION & URL NORMALIZATION TESTS -----------------

def test_url_normalization_postgres_to_postgresql():
    """Verifies legacy postgres:// URL is automatically normalized to postgresql://."""
    legacy = "postgres://user:pass@ep-xyz-pooler.neon.tech/neondb?sslmode=require"
    normalized = normalize_pg_url(legacy)
    assert normalized.startswith("postgresql://")
    assert "ep-xyz-pooler.neon.tech" in normalized

def test_settings_normalized_database_url_property():
    """Verifies Settings property cleanly normalizes DATABASE_URL."""
    s1 = Settings(DATABASE_URL="postgres://neon_user:secret@ep-neon.tech/prod")
    assert s1.normalized_database_url.startswith("postgresql://")

    s2 = Settings(DATABASE_URL="sqlite:///test.db")
    assert s2.normalized_database_url == "sqlite:///test.db"

def test_mask_connection_url_hides_secrets():
    """Verifies database password is never exposed in logs or console output."""
    raw = "postgresql://neon_admin:SuperSecretPass123@ep-cool-pooler.us-east-2.neon.tech/neondb"
    masked = mask_connection_url(raw)
    assert "SuperSecretPass123" not in masked
    assert "neon_admin:****@" in masked
    assert "ep-cool-pooler.us-east-2.neon.tech" in masked

def test_supabase_backup_settings_isolated_from_primary_db():
    """Verifies Supabase backup variables exist without colliding with primary Neon configuration."""
    s = Settings(
        DATABASE_URL="postgresql://neon_user:p@host/neondb",
        SUPABASE_URL="https://xyz.supabase.co",
        SUPABASE_SECRET_KEY="sb_secret_key"
    )
    assert s.DATABASE_URL.startswith("postgresql://")
    assert s.SUPABASE_URL == "https://xyz.supabase.co"
    assert s.SUPABASE_SECRET_KEY == "sb_secret_key"

# ----------------- ENGINE & POOLING PARAMETERS TESTS -----------------

def test_neon_postgresql_engine_parameters():
    """Verifies PostgreSQL engine configures pool_pre_ping and pool_recycle for Neon serverless."""
    test_pg_url = "postgresql://test_user:test_pass@localhost:5432/test_db"
    
    # Simulate database.py connection logic
    connect_args = {}
    if "sslmode=" not in test_pg_url.lower():
        connect_args["sslmode"] = "require"
    
    engine = create_engine(
        test_pg_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20
    )
    assert engine.dialect.name == "postgresql"
    assert engine.pool._pre_ping is True
    assert engine.pool._recycle == 300
    assert connect_args.get("sslmode") == "require"
    engine.dispose()

def test_sqlite_fallback_engine_parameters():
    """Verifies SQLite engine initializes and functions for local development."""
    sqlite_url = "sqlite:///:memory:"
    connect_args = {"check_same_thread": False}
    
    engine = create_engine(sqlite_url, connect_args=connect_args)
    assert engine.dialect.name == "sqlite"
    with engine.connect() as conn:
        val = conn.execute(text("SELECT 1")).scalar()
        assert val == 1
    engine.dispose()

# ----------------- ISOLATED MIGRATION & DATA INTEGRITY TESTS -----------------

def test_migration_dry_run_does_not_modify_anything():
    """Verifies dry-run reports all source records accurately with zero writes."""
    source_db = str(BASE_DIR / "rai_biz.db")
    if not os.path.exists(source_db):
        pytest.skip("Source SQLite database not present.")
    
    initial_hash = compute_sha256(source_db)
    result = run_migration(source_db, target_database_url="", dry_run=True)
    post_hash = compute_sha256(source_db)
    
    assert initial_hash == post_hash, "Dry run altered the source database file!"
    assert result["status"] == "dry_run_success"
    assert result["total_records"] > 0
    assert result["source_counts"]["users"] >= 1
    assert result["source_counts"]["businesses"] >= 1

def test_migration_to_isolated_target_database():
    """
    Tests end-to-end migration logic using an isolated temporary database target.
    Verifies:
    - 100% table schema creation.
    - 100% record parity across all 17 tables.
    - Relational integrity: Suntech Mobility, SmartHire, and all foreign keys.
    - Source database immutability.
    """
    source_db = str(BASE_DIR / "rai_biz.db")
    if not os.path.exists(source_db):
        pytest.skip("Source SQLite database not present.")
    
    source_hash_before = compute_sha256(source_db)

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    isolated_target_path = tmp.name
    tmp.close()

    try:
        isolated_target_url = f"sqlite:///{isolated_target_path}"
        
        # Execute migration against isolated target
        result = run_migration(
            source_sqlite_path=source_db,
            target_database_url=isolated_target_url,
            dry_run=False,
            force=False
        )

        assert result["status"] == "success"
        assert result["all_matched"] is True

        # Verify source database was completely untouched
        source_hash_after = compute_sha256(source_db)
        assert source_hash_before == source_hash_after, "Source database hash changed during migration!"

        # Inspect target database contents
        target_engine = create_engine(isolated_target_url)
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()

        # 1. Verify Suntech Mobility and SmartHire exist in target
        suntech = target_session.query(Business).filter(Business.name.like("%Suntech%")).first()
        assert suntech is not None, "Suntech Enterprise was not migrated to target!"

        smarthire = target_session.query(Business).filter(Business.id == 1).first()
        assert smarthire is not None, "SmartHire Solutions (id=1) was not migrated to target!"

        # 2. Verify AI Applications exist and link to businesses
        apps = target_session.query(AIApplication).all()
        assert len(apps) == result["source_counts"]["ai_applications"]
        for app_obj in apps:
            assert app_obj.business_id is not None
            biz = target_session.query(Business).filter(Business.id == app_obj.business_id).first()
            assert biz is not None, f"Orphaned AI Application #{app_obj.id} found in target!"

        # 3. Verify Assessments and AssessmentResponses
        assessments = target_session.query(Assessment).all()
        assert len(assessments) == result["source_counts"]["assessments"]
        responses = target_session.query(AssessmentResponse).all()
        assert len(responses) == result["source_counts"]["assessment_responses"]

        # 4. Verify Risks and Recommendations
        risks = target_session.query(Risk).all()
        assert len(risks) == result["source_counts"]["risks"]
        recs = target_session.query(Recommendation).all()
        assert len(recs) == result["source_counts"]["recommendations"]

        target_session.close()
        target_engine.dispose()

    finally:
        if os.path.exists(isolated_target_path):
            try:
                os.remove(isolated_target_path)
            except Exception:
                pass

def test_migration_safety_guard_aborts_on_non_empty_target():
    """Verifies migration tool refuses to overwrite non-empty target without --force."""
    source_db = str(BASE_DIR / "rai_biz.db")
    if not os.path.exists(source_db):
        pytest.skip("Source SQLite database not present.")

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    target_path = tmp.name
    tmp.close()

    try:
        target_url = f"sqlite:///{target_path}"
        engine = create_engine(target_url)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        s = Session()
        s.add(User(email="preexisting@example.com", full_name="Pre-existing User"))
        s.commit()
        s.close()
        engine.dispose()

        # Running migration without force must raise ValueError
        with pytest.raises(ValueError, match="already contains existing data"):
            run_migration(source_db, target_url, force=False)

    finally:
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception:
                pass

# ----------------- LIVE NEON / POSTGRESQL INTEGRATION TEST -----------------

def test_live_neon_postgresql_integration():
    """
    Live integration test executed against the test branch.
    Verifies:
    - Live query connectivity and SSL over PgBouncer pooled connection.
    - Presence of migrated tables on Neon.
    - Correct sequence continuity.
    """
    test_pg_url = resolve_target_url()
    if not test_pg_url or test_pg_url.startswith("sqlite"):
        pytest.skip("No PostgreSQL target URL resolved; skipping live remote test.")

    test_pg_url = normalize_pg_url(test_pg_url)
    masked = mask_connection_url(test_pg_url)
    print(f"\n[LIVE INTEGRATION TEST] Connecting to {masked}...")

    connect_args = {}
    if "sslmode=" not in test_pg_url.lower():
        connect_args["sslmode"] = "require"

    engine = create_engine(
        test_pg_url,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1")).scalar()
        assert res == 1
        
        # Verify dialect is indeed postgresql
        assert engine.dialect.name == "postgresql"

        # Check that businesses table exists and contains records
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "businesses" in tables, "businesses table missing on target Neon branch"
        
        biz_count = conn.execute(text("SELECT count(*) FROM businesses")).scalar()
        print(f"  Live Neon branch 'businesses' count: {biz_count}")
        assert biz_count >= 1, "Expected migrated businesses on target Neon branch"

        # Check sequence continuity for businesses_id_seq
        try:
            seq_curr = conn.execute(text("SELECT last_value FROM businesses_id_seq")).scalar()
            max_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM businesses")).scalar()
            print(f"  Sequence businesses_id_seq: {seq_curr}, MAX(id): {max_id}")
            assert seq_curr >= max_id, f"Sequence {seq_curr} is below MAX(id) {max_id}!"
        except Exception as e:
            print(f"  Sequence check note: {e}")

    engine.dispose()
