import logging
import os
import sys

# Add the project root to the python path so imports work when running this script directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import app.db.base  # This registers all SQLAlchemy models
from app.db.session import SessionLocal
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init() -> None:
    db = SessionLocal()
    
    # Check if a user already exists
    user = user_repo.get_by_email(db, email="admin@example.com")
    if not user:
        logger.info("Creating default admin user...")
        user_in = UserCreate(
            email="admin@example.com",
            name="Admin User",
            password="adminpassword123!",
            is_superuser=True,
        )
        user = user_repo.create(db, obj_in=user_in)
        logger.info(f"Admin user created with email: {user.email}")
    else:
        logger.info("Admin user already exists.")
        
    db.close()

if __name__ == "__main__":
    logger.info("Initializing database...")
    init()
    logger.info("Initialization complete.")
