from datetime import datetime, timezone
from uuid import uuid4

from app.data.store import (
    requests,
    donations,
    save_requests,
    save_donations,
)
from app.models.request import DonationRequest
from app.services.donation_service import (
    AVAILABLE,
    PARTIALLY_RESERVED,
    RESERVED,
    COMPLETED,
    CANCELLED,
    EXPIRED,
    get_remaining_quantity,
    reserve_quantity,
    release_quantity,
)


PENDING = "PENDING"
ACCEPTED = "ACCEPTED"
REJECTED = "REJECTED"
REQUEST_CANCELLED = "CANCELLED"
COLLECTION_CONFIRMED = "COLLECTION_CONFIRMED"
REQUEST_COMPLETED = "COMPLETED"


def get_request_by_id(
    request_id: str,
) -> DonationRequest | None:

    return next(
        (
            request
            for request in requests
            if request.id == request_id
        ),
        None,
    )


def get_requests_by_organization(
    organization_id: str,
) -> list[DonationRequest]:

    return [
        request
        for request in requests
        if request.organization_id == organization_id
    ]


def get_requests_by_donation(
    donation_id: str,
) -> list[DonationRequest]:

    return [
        request
        for request in requests
        if request.donation_id == donation_id
    ]


def _get_donation(
    donation_id: str,
) -> DonationRequest:

    donation = next(
        (
            donation
            for donation in donations
            if donation.id == donation_id
        ),
        None,
    )

    if donation is None:
        raise ValueError(
            "Donation not found."
        )

    return donation


def create_request(
    donation_id: str,
    organization_id: str,
    requested_quantity: int,
    collection_time: str,
    message: str = "",
) -> DonationRequest:

    if requested_quantity <= 0:
        raise ValueError(
            "Requested quantity must be greater than zero."
        )

    donation = _get_donation(
        donation_id
    )

    if donation.status in {
        CANCELLED,
        COMPLETED,
        EXPIRED,
    }:
        raise ValueError(
            "This donation is no longer available."
        )

    remaining_quantity = get_remaining_quantity(
        donation
    )

    if requested_quantity > remaining_quantity:
        raise ValueError(
            f"Only {remaining_quantity} {donation.unit} remaining."
        )

    request = DonationRequest(
        id=str(uuid4()),
        donation_id=donation_id,
        organization_id=organization_id,
        requested_quantity=requested_quantity,
        collection_time=collection_time,
        message=message,
        status=PENDING,
        created_at=datetime.now(timezone.utc),
    )

    requests.append(request)

    save_requests()

    return request


def accept_request(
    request_id: str,
    donor_id: str,
) -> DonationRequest:

    request = get_request_by_id(
        request_id
    )

    if request is None:
        raise ValueError(
            "Request not found."
        )

    donation = _get_donation(
        request.donation_id
    )

    if donation.donor_id != donor_id:
        raise ValueError(
            "You are not authorized to accept this request."
        )

    if request.status != PENDING:
        raise ValueError(
            "Only pending requests can be accepted."
        )

    remaining_quantity = get_remaining_quantity(
        donation
    )

    if request.requested_quantity > remaining_quantity:
        raise ValueError(
            f"Only {remaining_quantity} {donation.unit} remaining."
        )

    reserve_quantity(
        donation,
        request.requested_quantity,
    )

    request.status = ACCEPTED

    # Save both sides of the transaction.
    save_donations()
    save_requests()

    return request


def reject_request(
    request_id: str,
    donor_id: str,
) -> DonationRequest:

    request = get_request_by_id(
        request_id
    )

    if request is None:
        raise ValueError(
            "Request not found."
        )

    donation = _get_donation(
        request.donation_id
    )

    if donation.donor_id != donor_id:
        raise ValueError(
            "You are not authorized to reject this request."
        )

    if request.status != PENDING:
        raise ValueError(
            "Only pending requests can be rejected."
        )

    request.status = REJECTED

    save_requests()

    return request


def cancel_request(
    request_id: str,
    organization_id: str,
) -> DonationRequest:

    request = get_request_by_id(
        request_id
    )

    if request is None:
        raise ValueError(
            "Request not found."
        )

    if request.organization_id != organization_id:
        raise ValueError(
            "You are not authorized to cancel this request."
        )

    if request.status not in {
        PENDING,
        ACCEPTED,
    }:
        raise ValueError(
            "This request cannot be cancelled in its current status."
        )

    donation = _get_donation(
        request.donation_id
    )

    # Only an accepted request has reserved quantity.
    if request.status == ACCEPTED:
        release_quantity(
            donation,
            request.requested_quantity,
        )

    request.status = REQUEST_CANCELLED

    save_donations()
    save_requests()

    return request


def confirm_collection(
    request_id: str,
    organization_id: str,
) -> DonationRequest:

    request = get_request_by_id(
        request_id
    )

    if request is None:
        raise ValueError(
            "Request not found."
        )

    if request.organization_id != organization_id:
        raise ValueError(
            "You are not authorized to confirm collection."
        )

    if request.status != ACCEPTED:
        raise ValueError(
            "Only accepted requests can confirm collection."
        )

    request.status = COLLECTION_CONFIRMED

    save_requests()

    return request


def confirm_receipt(
    request_id: str,
    organization_id: str,
) -> DonationRequest:

    request = get_request_by_id(
        request_id
    )

    if request is None:
        raise ValueError(
            "Request not found."
        )

    if request.organization_id != organization_id:
        raise ValueError(
            "You are not authorized to confirm receipt."
        )

    if request.status != COLLECTION_CONFIRMED:
        raise ValueError(
            "Collection must be confirmed before receipt."
        )

    donation = _get_donation(
        request.donation_id
    )

    request.status = REQUEST_COMPLETED

    donation.status = COMPLETED

    save_donations()
    save_requests()

    return request