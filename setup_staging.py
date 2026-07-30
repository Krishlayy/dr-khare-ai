import asyncio
import os
import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings
from backend.database.models import User
from backend.core.security import get_password_hash

async def setup():
    # 1. Create S3 Bucket in MinIO
    if settings.AWS_ENDPOINT_URL:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_ENDPOINT_URL,
            region_name=settings.AWS_REGION
        )
        try:
            s3.create_bucket(Bucket=settings.AWS_BUCKET_NAME)
            print(f"Bucket {settings.AWS_BUCKET_NAME} created successfully.")
        except s3.exceptions.BucketAlreadyOwnedByYou:
            print(f"Bucket {settings.AWS_BUCKET_NAME} already exists.")
        except Exception as e:
            print(f"Error creating bucket: {e}")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # 2. Create Roles
    from backend.database.models import Role
    
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(name="admin", permissions="*")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)
        
    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        user_role = Role(name="user", permissions="chat")
        db.add(user_role)
        db.commit()

    # 3. Create Admin User
    admin_email = "admin@drkhare.com"
    existing = db.query(User).filter(User.email == admin_email).first()
    if not existing:
        admin_user = User(
            email=admin_email,
            password_hash=get_password_hash("admin123"),
            is_active=True,
            role_id=1,
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created: admin@drkhare.com / admin123")
    else:
        print("Admin user already exists.")
    db.close()

if __name__ == "__main__":
    asyncio.run(setup())
