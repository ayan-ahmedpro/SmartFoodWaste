from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.config import JWT_SECRET, JWT_ALGORITHM
from app.data.store import users, donations, requests
from app.services.request_service import (
    create_request,
    get_request_by_id,
    accept_request,
    reject_request,
    cancel_request,
    confirm_collection,
    confirm_receipt,
)

from app.schemas.request import DonationRequestCreate

router = APIRouter(
    prefix="/api",
    tags=["Requests"],
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


def serialize_request(request):
    return {
        "id": request.id,
        "donation_id": request.donation_id,
        "organization_id": request.organization_id,
        "requested_quantity": request.requested_quantity,
        "collection_time": request.collection_time,
        "message": request.message,
        "status": request.status,
        "created_at": request.created_at,
    }


@router.post(
    "/donations/{donation_id}/requests",
)
def create_donation_request(
    donation_id: str,
    data: DonationRequestCreate,
    current_user=Depends(get_current_user),
):
    if current_user.role != "organization":
        raise HTTPException(
            status_code=403,
            detail="Only organizations can submit donation requests.",
        )

    try:
        request = create_request(
            donation_id=donation_id,
            organization_id=current_user.id,
            requested_quantity=data.requested_quantity,
            collection_time=data.collection_time,
            message=data.message,
        )

        return {
            "success": True,
            "message": "Donation request submitted successfully.",
            "data": serialize_request(request),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/requests")
def get_requests(
    current_user=Depends(get_current_user),
):
    """
    Organizations see requests they submitted.

    Donors see requests submitted against their own donations.

    Admins see all requests.
    """

    if current_user.role == "organization":
        filtered_requests = [
            request
            for request in requests
            if request.organization_id == current_user.id
        ]

    elif current_user.role == "donor":
        donor_donation_ids = {
            donation.id
            for donation in donations
            if donation.donor_id == current_user.id
        }

        filtered_requests = [
            request
            for request in requests
            if request.donation_id in donor_donation_ids
        ]

    elif current_user.role == "admin":
        filtered_requests = list(requests)

    else:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view requests.",
        )

    return {
        "success": True,
        "data": [
            serialize_request(request)
            for request in filtered_requests
        ],
    }


@router.get("/requests/{request_id}")
def get_single_request(
    request_id: str,
    current_user=Depends(get_current_user),
):
    request = get_request_by_id(request_id)

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Request not found.",
        )

    if current_user.role == "organization":
        if request.organization_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to view this request.",
            )

    elif current_user.role == "donor":
        donation = next(
            (
                donation
                for donation in donations
                if donation.id == request.donation_id
            ),
            None,
        )

        if (
            donation is None
            or donation.donor_id != current_user.id
        ):
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to view this request.",
            )

    elif current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view this request.",
        )

    return {
        "success": True,
        "data": serialize_request(request),
    }


@router.post(
    "/requests/{request_id}/accept",
)
def accept_donation_request(
    request_id: str,
    current_user=Depends(get_current_user),
):
    if current_user.role != "donor":
        raise HTTPException(
            status_code=403,
            detail="Only donors can accept donation requests.",
        )

    try:
        request = accept_request(
            request_id=request_id,
            donor_id=current_user.id,
        )

        return {
            "success": True,
            "message": "Donation request accepted successfully.",
            "data": serialize_request(request),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post(
    "/requests/{request_id}/reject",
)
def reject_donation_request(
    request_id: str,
    current_user=Depends(get_current_user),
):
    if current_user.role != "donor":
        raise HTTPException(
            status_code=403,
            detail="Only donors can reject donation requests.",
        )

    try:
        request = reject_request(
            request_id=request_id,
            donor_id=current_user.id,
        )

        return {
            "success": True,
            "message": "Donation request rejected successfully.",
            "data": serialize_request(request),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post(
    "/requests/{request_id}/cancel",
)
def cancel_donation_request(
    request_id: str,
    current_user=Depends(get_current_user),
):
    if current_user.role != "organization":
        raise HTTPException(
            status_code=403,
            detail="Only organizations can cancel their requests.",
        )

    try:
        request = cancel_request(
            request_id=request_id,
            organization_id=current_user.id,
        )

        return {
            "success": True,
            "message": "Donation request cancelled successfully.",
            "data": serialize_request(request),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post(
    "/requests/{request_id}/confirm-collection",
)
def confirm_donation_collection(
    request_id: str,
    current_user=Depends(get_current_user),
):
    if current_user.role != "organization":
        raise HTTPException(
            status_code=403,
            detail="Only organizations can confirm collection.",
        )

    try:
        request = confirm_collection(
            request_id=request_id,
            organization_id=current_user.id,
        )

        return {
            "success": True,
            "message": "Collection confirmed successfully.",
            "data": serialize_request(request),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.post(
    "/requests/{request_id}/confirm-receipt",
)
def confirm_donation_receipt(
    request_id: str,
    current_user=Depends(get_current_user),
):
    if current_user.role != "organization":
        raise HTTPException(
            status_code=403,
            detail="Only organizations can confirm receipt.",
        )

    try:
        request = confirm_receipt(
            request_id=request_id,
            organization_id=current_user.id,
        )

        return {
            "success": True,
            "message": "Receipt confirmed successfully.",
            "data": serialize_request(request),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )