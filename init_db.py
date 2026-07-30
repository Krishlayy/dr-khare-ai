"""Initialize database tables, roles, and default admin user."""
from backend.core.security import get_password_hash
from backend.database.database import Base, SessionLocal, engine
import backend.database.models  # noqa: F401
from backend.database.models import Role, User

Base.metadata.create_all(bind=engine)
db = SessionLocal()

admin_role = db.query(Role).filter(Role.name == "Super Admin").first()
if not admin_role:
    admin_role = Role(name="Super Admin", permissions={"all": True})
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)

user_role = db.query(Role).filter(Role.name == "User").first()
if not user_role:
    user_role = Role(name="User", permissions={"chat": True})
    db.add(user_role)
    db.commit()

admin_user = db.query(User).filter(User.email == "admin@khare.ai").first()
if not admin_user:
    admin_user = User(
        email="admin@khare.ai",
        password_hash=get_password_hash("admin123"),
        role_id=admin_role.id,
    )
    db.add(admin_user)
else:
    admin_user.role_id = admin_role.id

db.commit()
db.close()
print("Database tables and admin user initialized successfully.")
print("Admin login: admin@khare.ai / admin123")
