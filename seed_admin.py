"""
seed_admin.py — Create the default admin user if not already present.
Safe to run multiple times (idempotent).

Usage (inside the running container):
  podman exec sf-portal-backend python seed_admin.py
"""
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password

ADMIN_EMPLOYEE_ID = "ADM001"
ADMIN_EMAIL = "admin@company.com"
ADMIN_PASSWORD = "Admin123"   # ← Change after first login!

db = SessionLocal()

try:
    existing = db.query(User).filter(User.employee_id == ADMIN_EMPLOYEE_ID).first()

    if existing:
        print(f"ℹ️  Admin '{ADMIN_EMPLOYEE_ID}' already exists — skipping.")
    else:
        admin = User(
            employee_id=ADMIN_EMPLOYEE_ID,
            name="System Admin",
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role="admin",
            status="active",
            must_change_password=False,
        )
        db.add(admin)
        db.commit()
        print(f"✅ Admin user '{ADMIN_EMPLOYEE_ID}' created successfully!")
        print(f"   Email:    {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}")
        print("   ⚠️  Please change the password after first login.")
finally:
    db.close()