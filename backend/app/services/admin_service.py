from datetime import datetime, timezone
from uuid import uuid4

from app.data.store import (
    users,
    donations,
    requests,
    audit_logs,
    save_users,
    save_donations,
    save_requests,
    save_audit_logs,
)

from app.services.donation_service import (
    AVAILABLE,
    PARTIALLY_RESERVED,
    RESERVED,
    COMPLETED,
    CANCELLED,
    EXPIRED,
    release_quantity,
)


# ================================================================
# USER STATUSES
# ================================================================

ACTIVE = "ACTIVE"
SUSPENDED = "SUSPENDED"
DEACTIVATED = "DEACTIVATED"


# ================================================================
# REQUEST STATUSES
# ================================================================

PENDING = "PENDING"
ACCEPTED = "ACCEPTED"
REJECTED = "REJECTED"
REQUEST_CANCELLED = "CANCELLED"
COLLECTION_CONFIRMED = "COLLECTION_CONFIRMED"
REQUEST_COMPLETED = "COMPLETED"


# ================================================================
# INTERNAL HELPERS
# ================================================================

def _get_user(user_id: str):
    return next(
        (
            user
            for user in users
            if user.id == user_id
        ),
        None,
    )


def _get_donation(donation_id: str):
    return next(
        (
            donation
            for donation in donations
            if donation.id == donation_id
        ),
        None,
    )


def _get_request(request_id: str):
    return next(
        (
            request
            for request in requests
            if request.id == request_id
        ),
        None,
    )


def _create_audit_log(
    admin_id: str,
    action: str,
    target_id: str,
    reason: str,
):
    audit_log = {
        "id": str(uuid4()),
        "admin_id": admin_id,
        "action": action,
        "target_id": target_id,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    audit_logs.append(audit_log)

    save_audit_logs()

    return audit_log


# ================================================================
# DASHBOARD
# ================================================================

def get_dashboard_stats():

    active_users = [
        user
        for user in users
        if user.status == ACTIVE
    ]

    active_donations = [
        donation
        for donation in donations
        if donation.status in {
            AVAILABLE,
            PARTIALLY_RESERVED,
            RESERVED,
        }
    ]

    pending_requests = [
        request
        for request in requests
        if request.status == PENDING
    ]

    completed_requests = [
        request
        for request in requests
        if request.status == REQUEST_COMPLETED
    ]

    return {
        "total_users": len(users),
        "active_users": len(active_users),
        "organizations": len(
            [
                user
                for user in users
                if user.role == "organization"
            ]
        ),
        "donors": len(
            [
                user
                for user in users
                if user.role == "donor"
            ]
        ),
        "total_donations": len(donations),
        "active_donations": len(active_donations),
        "total_requests": len(requests),
        "pending_requests": len(pending_requests),
        "completed_requests": len(completed_requests),
    }


# ================================================================
# USERS
# ================================================================

def get_all_users():

    return [
        user
        for user in users
    ]


def suspend_user(
    admin_id: str,
    user_id: str,
    reason: str,
):

    if not reason.strip():
        raise ValueError(
            "A reason is required for suspension."
        )

    user = _get_user(user_id)

    if user is None:
        raise ValueError(
            "User not found."
        )

    if user.role == "admin":
        raise ValueError(
            "Administrators cannot be suspended."
        )

    if user.status == DEACTIVATED:
        raise ValueError(
            "A deactivated account cannot be suspended."
        )

    if user.status == SUSPENDED:
        raise ValueError(
            "User is already suspended."
        )

    user.status = SUSPENDED

    save_users()

    _create_audit_log(
        admin_id=admin_id,
        action="SUSPEND_USER",
        target_id=user_id,
        reason=reason,
    )

    return user


def restore_user(
    admin_id: str,
    user_id: str,
    reason: str,
):

    if not reason.strip():
        raise ValueError(
            "A reason is required for restoration."
        )

    user = _get_user(user_id)

    if user is None:
        raise ValueError(
            "User not found."
        )

    if user.role == "admin":
        raise ValueError(
            "Administrators cannot be restored through this action."
        )

    if user.status == DEACTIVATED:
        raise ValueError(
            "A deactivated account cannot be restored."
        )

    if user.status != SUSPENDED:
        raise ValueError(
            "Only suspended users can be restored."
        )

    user.status = ACTIVE

    save_users()

    _create_audit_log(
        admin_id=admin_id,
        action="RESTORE_USER",
        target_id=user_id,
        reason=reason,
    )

    return user


def deactivate_user(
    admin_id: str,
    user_id: str,
    reason: str,
):

    if not reason.strip():
        raise ValueError(
            "A reason is required for deactivation."
        )

    user = _get_user(user_id)

    if user is None:
        raise ValueError(
            "User not found."
        )

    if user.role == "admin":
        raise ValueError(
            "Administrators cannot be deactivated."
        )

    if user.status == DEACTIVATED:
        raise ValueError(
            "User is already deactivated."
        )

    user.status = DEACTIVATED

    save_users()

    _create_audit_log(
        admin_id=admin_id,
        action="DEACTIVATE_USER",
        target_id=user_id,
        reason=reason,
    )

    return user


# ================================================================
# DONATIONS
# ================================================================

def get_all_donations():

    return [
        donation
        for donation in donations
    ]


def cancel_donation(
    admin_id: str,
    donation_id: str,
    reason: str,
):

    if not reason.strip():
        raise ValueError(
            "A reason is required for donation cancellation."
        )

    donation = _get_donation(
        donation_id
    )

    if donation is None:
        raise ValueError(
            "Donation not found."
        )

    if donation.status == CANCELLED:
        raise ValueError(
            "Donation is already cancelled."
        )

    if donation.status == COMPLETED:
        raise ValueError(
            "Completed donations cannot be cancelled."
        )

    # Cancel related requests.
    for request in requests:

        if request.donation_id != donation_id:
            continue

        if request.status == PENDING:

            request.status = REQUEST_CANCELLED

        elif request.status == ACCEPTED:

            release_quantity(
                donation,
                request.requested_quantity,
            )

            request.status = REQUEST_CANCELLED

    donation.status = CANCELLED

    save_donations()
    save_requests()

    _create_audit_log(
        admin_id=admin_id,
        action="CANCEL_DONATION",
        target_id=donation_id,
        reason=reason,
    )

    return donation


# ================================================================
# REQUESTS
# ================================================================

def get_all_requests():

    return [
        request
        for request in requests
    ]


def cancel_request(
    admin_id: str,
    request_id: str,
    reason: str,
):

    if not reason.strip():
        raise ValueError(
            "A reason is required for request cancellation."
        )

    request = _get_request(
        request_id
    )

    if request is None:
        raise ValueError(
            "Request not found."
        )

    if request.status in {
        REQUEST_CANCELLED,
        REJECTED,
        REQUEST_COMPLETED,
    }:

        raise ValueError(
            "This request cannot be cancelled."
        )

    donation = _get_donation(
        request.donation_id
    )

    if donation is None:
        raise ValueError(
            "Related donation not found."
        )

    # Release reserved quantity if the request
    # has already been accepted.
    if request.status in {
        ACCEPTED,
        COLLECTION_CONFIRMED,
    }:

        release_quantity(
            donation,
            request.requested_quantity,
        )

    request.status = REQUEST_CANCELLED

    save_donations()
    save_requests()

    _create_audit_log(
        admin_id=admin_id,
        action="CANCEL_REQUEST",
        target_id=request_id,
        reason=reason,
    )

    return request


# ================================================================
# AUDIT LOGS
# ================================================================

def get_audit_logs():

    return [
        log
        for log in audit_logs
    ]