from sqlalchemy.orm import Session
from app.database import get_db, engine  # Import your database setup
from app import models, helper_functions  # Adjust imports as per your project structure

# Ensure your models are created in the database
models.Base.metadata.create_all(bind=engine)

def create_initial_admin():
    db: Session = next(get_db())
    try:
        # Check if an admin user already exists
        existing_admin = db.query(models.Admin).filter_by(username="superadmin").first()
        if existing_admin:
            print("Admin user already exists.")
            return

        # Create new admin user with hashed password
        hashed_password = helper_functions.hash_password("YourSecurePassword")
        new_admin = models.Admin(
            username="superadmin",
            email="superadmin@example.com",
            password=hashed_password,
            role="admin"
        )

        db.add(new_admin)
        db.commit()
        print("Initial admin user created successfully.")
    except Exception as e:
        db.rollback()
        print(f"Failed to create admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_admin()
