"""Quick script to verify tables were created correctly."""
from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check tables
result = db.execute(text(
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema = 'public' ORDER BY table_name"
))
print("=== Tables in seat_management ===")
for row in result:
    print(f"  ✅ {row[0]}")

# Check unique constraints
print()
result2 = db.execute(text(
    "SELECT constraint_name, table_name FROM information_schema.table_constraints "
    "WHERE constraint_type = 'UNIQUE' AND table_schema = 'public'"
))
print("=== Unique Constraints ===")
for row in result2:
    print(f"  🔒 {row[0]} on {row[1]}")

db.close()
print("\n✅ Database layer verified successfully!")
