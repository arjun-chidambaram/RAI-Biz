# RAI-Biz Database Migration & Supabase PostgreSQL Backup Test Plan

**Document Type:** Database Architecture & Reliability Engineering Specification  
**Current Production Database:** SQLite 3 (`backend/rai_biz.db`, SHA-256: `8305B703112C93B604E651933A8FECE9A93151AF8D5D255B3B457240F89B0997`)  
**Target Architecture:** Hosted PostgreSQL (Supabase / Render Managed Postgres)  
**Objective:** Provide a non-disruptive, verifiable migration, backup, and restore strategy preserving all existing Suntech Mobility and SmartHire records.

---

## 1. Migration Architecture & Rationale

While SQLite provides reliable zero-configuration local persistence, migrating to hosted PostgreSQL / Supabase provides:
1. **Persistent Serverless Storage:** Avoids ephemeral disk resetting on container restarts.
2. **Concurrent Transactional Capacity:** Eliminates SQLite file locking (`database is locked`) during concurrent multi-tenant audit evaluations.
3. **Automated Point-in-Time Recovery (PITR):** Enables daily encrypted snapshots and automated rollback.
4. **Enhanced Row-Level Security (RLS):** Allows future native PostgreSQL RLS policies to supplement API layer authorization.

```mermaid
graph LR
    subgraph Current_State[Current Architecture]
        FastAPI_App[FastAPI Backend on Render] -->|SQLAlchemy 2.0| SQLite_DB[(rai_biz.db - Local Persistent Disk)]
    end

    subgraph Migration_Pipeline[Automated Migration Pipeline]
        Backup[1. Cryptographic Snapshot] --> Export[2. JSON/SQL DDL Export]
        Export --> Transform[3. Type Mapping & Schema Conversion]
        Transform --> Import[4. Supabase PostgreSQL Ingestion]
        Import --> Verify[5. Automated Verification Suite]
    end

    subgraph Target_State[Target Architecture]
        FastAPI_Target[FastAPI Backend on Render] -->|pg8000 / asyncpg| Supabase_Postgres[(Supabase PostgreSQL Database)]
        Supabase_Postgres --> PITR[Automated Hourly PITR Backups]
    end

    Current_State --> Migration_Pipeline --> Target_State
```

---

## 2. SQLite to PostgreSQL Type Mapping Specification

SQLAlchemy models in `backend/app/models.py` were written using standard SQL types that translate seamlessly between SQLite and PostgreSQL:

| Model Column Type | SQLite Implementation | PostgreSQL / Supabase Target | Notes |
|---|---|---|---|
| `Integer`, primary key | `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` or `IDENTITY` | Auto-increments seamlessly |
| `String(255)` | `VARCHAR(255)` | `VARCHAR(255)` | Identical semantics |
| `Text` | `TEXT` | `TEXT` | Identical unbounded text |
| `Float` | `REAL` | `DOUBLE PRECISION` or `NUMERIC(10,4)` | Exact precision |
| `Boolean` | `INTEGER` (0 or 1) | `BOOLEAN` (TRUE or FALSE) | SQLAlchemy handles coercion |
| `DateTime` | `VARCHAR` (ISO 8601 string) | `TIMESTAMP WITHOUT TIME ZONE` | Standard UTC timestamps |
| `JSON` (stored as `Text`) | `TEXT` | `JSONB` or `TEXT` | `remediation_history_json`, etc. |

---

## 3. Step-by-Step Migration & Backup Procedure

### Phase 1: Cryptographic Backup & Freezing
1. Compute and record SHA-256 hash of `backend/rai_biz.db`:
   ```powershell
   Get-FileHash -Algorithm SHA256 backend/rai_biz.db
   ```
2. Create immutable timestamped cold backup:
   ```powershell
   Copy-Item backend/rai_biz.db "backend/rai_biz.db.bak_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
   ```

### Phase 2: Supabase Provisioning
1. Provision Supabase project under region close to Render backend (e.g. `eu-central-1` or `us-east-1`).
2. Retrieve connection string:
   `postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres`
3. Configure `DATABASE_URL` in environment variables.

### Phase 3: Schema Creation & Data Transfer
A dedicated script (`backend/migrate_to_postgres.py`) will perform the transfer:
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import (
    User, Business, BusinessUser, AIApplication, Assessment,
    AssessmentResponse, Dataset, Risk, Recommendation
)

SQLITE_URL = "sqlite:///rai_biz.db"
POSTGRES_URL = os.getenv("SUPABASE_DATABASE_URL")

sqlite_engine = create_engine(SQLITE_URL)
pg_engine = create_engine(POSTGRES_URL)

# 1. Create tables in PostgreSQL
Base.metadata.create_all(bind=pg_engine)

# 2. Transfer rows in foreign key dependency order
# Order: User -> Business -> BusinessUser -> AIApplication -> Assessment -> AssessmentResponse -> Dataset -> Risk -> Recommendation
```

### Phase 4: Verification Suite on PostgreSQL
Run the complete automated test suite against PostgreSQL before switching production traffic:
```powershell
$env:DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres"
python -m pytest backend/tests/ -v
```
All 86 test cases must pass 100%.

### Phase 5: Zero-Downtime Traffic Cutover
1. Update Render environment variable `DATABASE_URL` to point to Supabase connection string.
2. Trigger Render rolling deployment.
3. Verify Render `/health` reports:
   ```json
   {
     "status": "healthy",
     "service": "RAI-Biz API",
     "database": "connected"
   }
   ```
4. Perform smoke test on `https://rai-biz.vercel.app`.

---

## 4. Rollback & Disaster Recovery Protocol

If any latency spike, connection drop, or serialization issue occurs:
1. Immediately revert Render `DATABASE_URL` to `sqlite:///rai_biz.db`.
2. Redeploy backend (latency to rollback < 60 seconds).
3. The original SQLite database remains completely intact with its verified SHA-256 hash.
4. No user or assessment data is lost.
