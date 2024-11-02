# create_super_admin.py
from app.database import SessionLocal
from app import models
from app.helper_functions import hash_password  
# Initialize a database session
db = SessionLocal()

# Check if a super admin already exists

existing_super_admin = db.query(models.Admin).filter(models.Admin.role == "superadmin").first()
if not existing_super_admin:
    # Define your super admin credentials
    super_admin = models.Admin(
        username="superadmin",
        email="superadmin@gmail.com",
        password=hash_password("SECUREPASSWORD"),
        role="superadmin"

    )

    db.add(super_admin)
    db.commit()
    print("Super admin created successfully.")
else:
    print("Super admin already exists.")

db.close()
