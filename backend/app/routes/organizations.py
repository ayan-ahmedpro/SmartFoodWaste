from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import jwt

from app.config import JWT_SECRET, JWT_ALGORITHM
from app.data.store import users
from app.services.organization_service import organization_service


router = APIRouter(
    prefix="/api/organizations",
    tags=["Organizations"],
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

        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )


# -------------------------------------------------------------------
# Get all organizations
# -------------------------------------------------------------------

@router.get("")
def get_organizations(
    current_user=Depends(get_current_user),
):
    organizations = []

    for user in users:

        if user.role != "organization":
            continue

        profile = organization_service.get_profile(
            user.id
        )

        organizations.append(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "accepted_food_categories": (
                    profile.accepted_food_categories
                    if profile
                    else []
                ),
                "dietary_requirements": (
                    profile.dietary_requirements
                    if profile
                    else []
                ),
                "minimum_quantity": (
                    profile.minimum_quantity
                    if profile
                    else 0
                ),
                "latitude": (
                    profile.latitude
                    if profile
                    else None
                ),
                "longitude": (
                    profile.longitude
                    if profile
                    else None
                ),
            }
        )

    return {
        "success": True,
        "data": organizations,
    }


# -------------------------------------------------------------------
# Get a specific organization
# -------------------------------------------------------------------

@router.get("/{organization_id}")
def get_organization(
    organization_id: str,
    current_user=Depends(get_current_user),
):
    organization = next(
        (
            user
            for user in users
            if user.id == organization_id
            and user.role == "organization"
        ),
        None,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found.",
        )

    profile = organization_service.get_profile(
        organization.id
    )

    return {
        "success": True,
        "data": {
            "id": organization.id,
            "name": organization.name,
            "email": organization.email,
            "role": organization.role,
            "accepted_food_categories": (
                profile.accepted_food_categories
                if profile
                else []
            ),
            "dietary_requirements": (
                profile.dietary_requirements
                if profile
                else []
            ),
            "minimum_quantity": (
                profile.minimum_quantity
                if profile
                else 0
            ),
            "latitude": (
                profile.latitude
                if profile
                else None
            ),
            "longitude": (
                profile.longitude
                if profile
                else None
            ),
        },
    }


# -------------------------------------------------------------------
# Get current organization's profile
# -------------------------------------------------------------------

@router.get("/me/profile")
def get_my_profile(
    current_user=Depends(get_current_user),
):
    user_id = current_user.get("user_id")
    role = current_user.get("role")

    if role != "organization":
        raise HTTPException(
            status_code=403,
            detail="Only organizations can access this profile.",
        )

    organization = next(
        (
            user
            for user in users
            if user.id == user_id
            and user.role == "organization"
        ),
        None,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization account not found.",
        )

    profile = organization_service.get_or_create_profile(
        organization.id
    )

    return {
        "success": True,
        "data": {
            "id": organization.id,
            "name": organization.name,
            "email": organization.email,
            "role": organization.role,
            "accepted_food_categories": (
                profile.accepted_food_categories
            ),
            "dietary_requirements": (
                profile.dietary_requirements
            ),
            "minimum_quantity": (
                profile.minimum_quantity
            ),
            "latitude": profile.latitude,
            "longitude": profile.longitude,
        },
    }


# -------------------------------------------------------------------
# Update current organization's profile
# -------------------------------------------------------------------

@router.put("/me/profile")
def update_my_profile(
    data: dict,
    current_user=Depends(get_current_user),
):
    user_id = current_user.get("user_id")
    role = current_user.get("role")

    if role != "organization":
        raise HTTPException(
            status_code=403,
            detail="Only organizations can update this profile.",
        )

    organization = next(
        (
            user
            for user in users
            if user.id == user_id
            and user.role == "organization"
        ),
        None,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization account not found.",
        )

    try:
        profile = organization_service.update_profile(
            user_id=organization.id,
            data=data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "success": True,
        "message": "Organization profile updated successfully.",
        "data": {
            "id": organization.id,
            "name": organization.name,
            "email": organization.email,
            "role": organization.role,
            "accepted_food_categories": (
                profile.accepted_food_categories
            ),
            "dietary_requirements": (
                profile.dietary_requirements
            ),
            "minimum_quantity": (
                profile.minimum_quantity
            ),
            "latitude": profile.latitude,
            "longitude": profile.longitude,
        },
    }