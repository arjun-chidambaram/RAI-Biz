import re
from app.models import Base
from app.main import app

print("=== SQLALCHEMY MODELS ===")
for table_name, table in Base.metadata.tables.items():
    fks = [f"{c.name}->{list(c.foreign_keys)[0].target_fullname}" for c in table.columns if c.foreign_keys]
    fk_str = f" [FKs: {', '.join(fks)}]" if fks else ""
    print(f"Table: {table_name:25} ({len(table.columns)} columns){fk_str}")

print("\n=== FASTAPI REGISTERED ROUTES ===")
for r in app.routes:
    if hasattr(r, 'methods'):
        methods = ",".join(sorted(r.methods))
        print(f"{methods:15} {r.path}")

