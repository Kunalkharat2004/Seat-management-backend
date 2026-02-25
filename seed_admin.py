# seed_admin.py
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password

db = SessionLocal()
admin = User(
    employee_id="ADM001",
    name="System Admin",
    email="admin@company.com",
    password_hash=hash_password("Admin123"), # Using our security utility
    role="admin",
    status="active",
    must_change_password=False
)
db.add(admin)
db.commit()
print("✅ Admin user ADM001 created!")
db.close()