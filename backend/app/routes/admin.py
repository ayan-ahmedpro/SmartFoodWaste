from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import jwt

from app.config import JWT_SECRET, JWT_ALGORITHM
from app.services.admin_service import (
    get_dashboard_stats,
    get_all_users,
    suspend_user,
    restore_user,
    deactivate_user,
    get_all_donations,
    cancel_donation,
    get_all_requests,
    cancel_request,
    get_audit_logs,
)


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Decode and validate the JWT token.
    """

    try:
        return jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )


def require_admin(
    current_user=Depends(get_current_user),
):
    """
    Allow only authenticated administrators.
    """

    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can perform this action.",
        )

    return current_user


@router.get("/dashboard")
def admin_dashboard(
    current_user=Depends(require_admin),
):
    """
    Get platform-wide admin statistics.
    """

    return {
        "success": True,
        "data": get_dashboard_stats(),
    }


@router.get("/users")
def admin_users(
    current_user=Depends(require_admin),
):
    """
    Get all registered users.
    """

    return {
        "success": True,
        "data": get_all_users(),
    }


@router.patch("/users/{user_id}/suspend")
def admin_suspend_user(
    user_id: str,
    reason: str,
    current_user=Depends(require_admin),
):
    """
    Suspend a user account.
    """

    try:
        user = suspend_user(
            admin_id=current_user["user_id"],
            user_id=user_id,
            reason=reason,
        )

        return {
            "success": True,
            "message": "User suspended successfully.",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "status": user.status,
            },
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.patch("/users/{user_id}/restore")
def admin_restore_user(
    user_id: str,
    reason: str,
    current_user=Depends(require_admin),
):
    """
    Restore a suspended user.
    """

    try:
        user = restore_user(
            admin_id=current_user["user_id"],
            user_id=user_id,
            reason=reason,
        )

        return {
            "success": True,
            "message": "User restored successfully.",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "status": user.status,
            },
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.patch("/users/{user_id}/deactivate")
def admin_deactivate_user(
    user_id: str,
    reason: str,
    current_user=Depends(require_admin),
):
    """
    Deactivate a user account.
    """

    try:
        user = deactivate_user(
            admin_id=current_user["user_id"],
            user_id=user_id,
            reason=reason,
        )

        return {
            "success": True,
            "message": "User deactivated successfully.",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "status": user.status,
            },
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/donations")
def admin_donations(
    current_user=Depends(require_admin),
):
    """
    Get all donations.
    """

    return {
        "success": True,
        "data": get_all_donations(),
    }


@router.patch("/donations/{donation_id}/cancel")
def admin_cancel_donation(
    donation_id: str,
    reason: str,
    current_user=Depends(require_admin),
):
    """
    Cancel a donation as an administrator.
    """

    try:
        donation = cancel_donation(
            admin_id=current_user["user_id"],
            donation_id=donation_id,
            reason=reason,
        )

        return {
            "success": True,
            "message": "Donation cancelled successfully.",
            "data": {
                "id": donation.id,
                "food_name": donation.food_name,
                "status": donation.status,
            },
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/requests")
def admin_requests(
    current_user=Depends(require_admin),
):
    """
    Get all donation requests.
    """

    return {
        "success": True,
        "data": get_all_requests(),
    }


@router.patch("/requests/{request_id}/cancel")
def admin_cancel_request(
    request_id: str,
    reason: str,
    current_user=Depends(require_admin),
):
    """
    Cancel a donation request as an administrator.
    """

    try:
        request = cancel_request(
            admin_id=current_user["user_id"],
            request_id=request_id,
            reason=reason,
        )

        return {
            "success": True,
            "message": "Request cancelled successfully.",
            "data": {
                "id": request.id,
                "status": request.status,
            },
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("/audit-logs")
def admin_audit_logs(
    current_user=Depends(require_admin),
):
    """
    Get administrator activity logs.
    """

    return {
        "success": True,
        "data": get_audit_logs(),
    }