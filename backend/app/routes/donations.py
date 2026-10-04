from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

import jwt

from app.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
)

from app.schemas.donation import (
    DonationCreate,
    DonationUpdate,
)

from app.services.donation_service import (
    create_donation,
    get_donor_donations,
    update_donation,
    cancel_donation,
    update_expired_status,
)


router = APIRouter(
    prefix="/api/donations",
    tags=["Donations"],
)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
):
    """
    Validate the JWT token and return its payload.

    This dependency is used for endpoints that can be accessed
    by authenticated users regardless of their role.
    """

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get(
            "user_id"
        )

        role = payload.get(
            "role"
        )

        if not user_id or not role:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token.",
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired.",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )


def require_donor(
    current_user=Depends(
        get_current_user
    ),
):
    """
    Restrict an endpoint to donor accounts.
    """

    if current_user.get("role") != "donor":
        raise HTTPException(
            status_code=403,
            detail="Only donors can perform this action.",
        )

    return current_user


@router.post("")
def create_donation_route(
    data: DonationCreate,
    current_user=Depends(
        require_donor
    ),
):
    """
    Create a new food donation.

    Only donors are allowed to create donations.
    """

    try:
        donation = create_donation(
            donor_id=current_user["user_id"],
            food_name=data.food_name,
            category=data.category,
            quantity=data.quantity,
            unit=data.unit,
            preparation_datetime=(
                data.preparation_datetime
            ),
            safe_consumption_deadline=(
                data.safe_consumption_deadline
            ),
            pickup_address=data.pickup_address,
            storage_instructions=(
                data.storage_instructions
            ),
            dietary_information=(
                data.dietary_information
            ),
            description=data.description,
            latitude=data.latitude,
            longitude=data.longitude,
        )

        return {
            "success": True,
            "message": (
                "Donation created successfully."
            ),
            "data": donation.model_dump(),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("")
def get_donations(
    current_user=Depends(
        get_current_user
    ),
):
    """
    Get donations visible to the authenticated user.

    Organizations:
        Can browse available donations.

    Donors:
        Can see their own donations.

    Admins:
        Can see available donations through this endpoint.
        Admin-specific full donation management remains under
        the admin routes.
    """

    role = current_user.get(
        "role"
    )

    user_id = current_user.get(
        "user_id"
    )

    if role == "donor":

        donations = get_donor_donations(
            user_id
        )

    else:
        from app.data.store import donations

        donations = list(
            donations
        )

        for donation in donations:
            update_expired_status(
                donation
            )

    return {
        "success": True,
        "data": [
            donation.model_dump()
            for donation in donations
        ],
    }


@router.get("/{donation_id}")
def get_donation(
    donation_id: str,
    current_user=Depends(
        get_current_user
    ),
):
    """
    Get a single donation.

    Donors:
        Can view their own donation.

    Organizations:
        Can view donations so they can inspect and request them.

    Admins:
        Can view donations.

    Backend authorization is still enforced for update/cancel
    operations separately.
    """

    from app.data.store import donations

    donation = next(
        (
            item
            for item in donations
            if item.id == donation_id
        ),
        None,
    )

    if donation is None:
        raise HTTPException(
            status_code=404,
            detail="Donation not found.",
        )

    update_expired_status(
        donation
    )

    return {
        "success": True,
        "data": donation.model_dump(),
    }


@router.patch("/{donation_id}")
def update_my_donation(
    donation_id: str,
    data: DonationUpdate,
    current_user=Depends(
        require_donor
    ),
):
    """
    Update a donation.

    Only the donor who owns the donation can update it.
    Ownership is checked inside the service layer.
    """

    updates = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    try:
        donation = update_donation(
            donation_id=donation_id,
            donor_id=current_user["user_id"],
            updates=updates,
        )

        return {
            "success": True,
            "message": (
                "Donation updated successfully."
            ),
            "data": donation.model_dump(),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.patch(
    "/{donation_id}/cancel"
)
def cancel_my_donation(
    donation_id: str,
    current_user=Depends(
        require_donor
    ),
):
    """
    Cancel a donation.

    Only the donor who owns the donation can cancel it.
    """

    try:
        donation = cancel_donation(
            donation_id,
            current_user["user_id"],
        )

        return {
            "success": True,
            "message": (
                "Donation cancelled successfully."
            ),
            "data": donation.model_dump(),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )