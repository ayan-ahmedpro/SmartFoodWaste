from uuid import uuid4

from app.data.store import users, save_users
from app.models.user import User
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
)


ALLOWED_SIGNUP_ROLES = {"organization", "donor"}

ACTIVE = "ACTIVE"
SUSPENDED = "SUSPENDED"
DEACTIVATED = "DEACTIVATED"


def signup(
    name: str,
    email: str,
    password: str,
    role: str,
) -> User:

    # ---------------------------------------------------------------
    # Validate signup role
    # ---------------------------------------------------------------

    if role not in ALLOWED_SIGNUP_ROLES:
        raise ValueError(
            "You can only sign up as an organization or donor."
        )

    # ---------------------------------------------------------------
    # Prevent duplicate accounts
    # ---------------------------------------------------------------

    existing_user = next(
        (
            user
            for user in users
            if user.email.lower() == email.lower()
        ),
        None,
    )

    if existing_user:
        raise ValueError(
            "An account with this email already exists."
        )

    # ---------------------------------------------------------------
    # Create user
    # ---------------------------------------------------------------

    user = User(
        id=str(uuid4()),
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        status=ACTIVE,
    )

    users.append(user)

    # ---------------------------------------------------------------
    # IMPORTANT:
    # Persist the new user to users.json
    # ---------------------------------------------------------------

    save_users()

    return user


def login(
    email: str,
    password: str,
) -> str:

    # ---------------------------------------------------------------
    # Find user
    # ---------------------------------------------------------------

    user = next(
        (
            user
            for user in users
            if user.email.lower() == email.lower()
        ),
        None,
    )

    if user is None:
        raise ValueError(
            "Invalid email or password."
        )

    # ---------------------------------------------------------------
    # Check account status
    # ---------------------------------------------------------------

    user_status = getattr(
        user,
        "status",
        ACTIVE,
    )

    if user_status == SUSPENDED:
        raise ValueError(
            "Your account has been suspended. "
            "Please contact the administrator."
        )

    if user_status == DEACTIVATED:
        raise ValueError(
            "Your account has been deactivated."
        )

    # ---------------------------------------------------------------
    # Verify password
    # ---------------------------------------------------------------

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise ValueError(
            "Invalid email or password."
        )

    # ---------------------------------------------------------------
    # Generate JWT
    # ---------------------------------------------------------------

    return create_access_token(
        user_id=user.id,
        role=user.role,
    )