from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.config import JWT_SECRET, JWT_ALGORITHM
from app.data.store import users

from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
)

from app.services.auth_service import (
    signup,
    login,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token.",
            )

        user = next(
            (
                user
                for user in users
                if user.id == user_id
            ),
            None,
        )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="User account not found.",
            )

        if user.status != "ACTIVE":
            raise HTTPException(
                status_code=403,
                detail="Your account is not active.",
            )

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired.",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token.",
        )


@router.post("/signup")
def signup_user(data: SignupRequest):
    try:
        user = signup(
            name=data.name,
            email=data.email,
            password=data.password,
            role=data.role,
        )

        return {
            "success": True,
            "message": "Account created successfully.",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            },
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post("/login")
def login_user(data: LoginRequest):
    try:
        token = login(
            email=data.email,
            password=data.password,
        )

        return {
            "success": True,
            "message": "Login successful.",
            "data": {
                "access_token": token,
                "token_type": "bearer",
            },
        }

    except ValueError as error:
        raise HTTPException(
            status_code=401,
            detail=str(error),
        )


@router.get("/me")
def get_me(
    current_user=Depends(get_current_user),
):
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "status": current_user.status,
        },
    }