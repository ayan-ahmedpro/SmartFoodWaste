from uuid import uuid4

from app.data.store import users, save_users
from app.models.user import User
from app.utils.security import hash_password


DEMO_ADMIN_EMAIL = "admin@example.com"
DEMO_ADMIN_PASSWORD = "admin123"


def seed_demo_admin():
    existing_admin = next(
        (
            user
            for user in users
            if user.email.lower() == DEMO_ADMIN_EMAIL.lower()
        ),
        None,
    )

    if existing_admin is not None:
        return existing_admin

    admin = User(
        id=str(uuid4()),
        name="Demo Administrator",
        email=DEMO_ADMIN_EMAIL,
        password_hash=hash_password(DEMO_ADMIN_PASSWORD),
        role="admin",
        status="ACTIVE",
    )

    users.append(admin)

    # Persist the seeded administrator.
    save_users()

    return admin


def seed_demo_data():
    seed_demo_admin()