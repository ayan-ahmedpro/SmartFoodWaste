from datetime import datetime, timezone
from uuid import uuid4

from app.data.store import (
    donations,
    save_donations,
)
from app.models.donation import Donation


AVAILABLE = "AVAILABLE"
PARTIALLY_RESERVED = "PARTIALLY_RESERVED"
RESERVED = "RESERVED"
COMPLETED = "COMPLETED"
CANCELLED = "CANCELLED"
EXPIRED = "EXPIRED"


def _make_aware(
    value: datetime,
) -> datetime:
    """
    Convert a naive datetime into a UTC-aware datetime.
    """

    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value


def update_expired_status(
    donation: Donation,
) -> Donation:
    """
    Mark an available donation as expired when its
    safe-consumption deadline has passed.
    """

    if donation.status in {
        AVAILABLE,
        PARTIALLY_RESERVED,
    }:
        now = datetime.now(
            timezone.utc
        )

        deadline = _make_aware(
            donation.safe_consumption_deadline
        )

        if deadline <= now:
            donation.status = EXPIRED
            save_donations()

    return donation


def _validate_coordinates(
    latitude: float | None,
    longitude: float | None,
) -> tuple[float | None, float | None]:
    """
    Validate optional geographic coordinates.

    Coordinates are optional because an existing donation
    may not have location information.
    """

    if latitude is None:
        validated_latitude = None
    else:
        try:
            validated_latitude = float(
                latitude
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "Latitude must be a number."
            ) from error

        if not -90 <= validated_latitude <= 90:
            raise ValueError(
                "Latitude must be between -90 and 90."
            )

    if longitude is None:
        validated_longitude = None
    else:
        try:
            validated_longitude = float(
                longitude
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "Longitude must be a number."
            ) from error

        if not -180 <= validated_longitude <= 180:
            raise ValueError(
                "Longitude must be between -180 and 180."
            )

    return (
        validated_latitude,
        validated_longitude,
    )


def create_donation(
    donor_id: str,
    food_name: str,
    category: str,
    quantity: int,
    unit: str,
    preparation_datetime: datetime,
    safe_consumption_deadline: datetime,
    pickup_address: str,
    storage_instructions: str,
    dietary_information: str,
    description: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Donation:

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    preparation = _make_aware(
        preparation_datetime
    )

    deadline = _make_aware(
        safe_consumption_deadline
    )

    if deadline <= preparation:
        raise ValueError(
            "Safe consumption deadline must be after "
            "the preparation time."
        )

    (
        validated_latitude,
        validated_longitude,
    ) = _validate_coordinates(
        latitude,
        longitude,
    )

    donation = Donation(
        id=str(uuid4()),
        donor_id=donor_id,
        food_name=food_name,
        category=category,
        quantity=quantity,
        reserved_quantity=0,
        unit=unit,
        preparation_datetime=preparation_datetime,
        safe_consumption_deadline=safe_consumption_deadline,
        pickup_address=pickup_address,
        latitude=validated_latitude,
        longitude=validated_longitude,
        storage_instructions=storage_instructions,
        dietary_information=dietary_information,
        description=description,
        status=AVAILABLE,
    )

    donations.append(
        donation
    )

    save_donations()

    return donation


def get_donation_by_id(
    donation_id: str,
) -> Donation | None:

    donation = next(
        (
            donation
            for donation in donations
            if donation.id == donation_id
        ),
        None,
    )

    if donation is not None:
        update_expired_status(
            donation
        )

    return donation


def get_donor_donations(
    donor_id: str,
) -> list[Donation]:
    """
    Get all donations belonging to a specific donor.

    This function name is kept for compatibility with
    the existing donations route.
    """

    donor_donations = [
        donation
        for donation in donations
        if donation.donor_id == donor_id
    ]

    for donation in donor_donations:
        update_expired_status(
            donation
        )

    return donor_donations


def get_all_donations() -> list[Donation]:

    for donation in donations:
        update_expired_status(
            donation
        )

    return donations


def update_donation(
    donation_id: str,
    donor_id: str,
    updates: dict,
) -> Donation:

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

    if donation.donor_id != donor_id:
        raise ValueError(
            "You are not authorized to update this donation."
        )

    if donation.status != AVAILABLE:
        raise ValueError(
            "Only available donations can be updated."
        )

    for field, value in updates.items():

        if value is None:
            continue

        if field == "quantity" and value <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        if field == "latitude":
            try:
                value = float(
                    value
                )
            except (
                TypeError,
                ValueError,
            ) as error:
                raise ValueError(
                    "Latitude must be a number."
                ) from error

            if not -90 <= value <= 90:
                raise ValueError(
                    "Latitude must be between -90 and 90."
                )

        if field == "longitude":
            try:
                value = float(
                    value
                )
            except (
                TypeError,
                ValueError,
            ) as error:
                raise ValueError(
                    "Longitude must be a number."
                ) from error

            if not -180 <= value <= 180:
                raise ValueError(
                    "Longitude must be between -180 and 180."
                )

        if hasattr(
            donation,
            field,
        ):
            setattr(
                donation,
                field,
                value,
            )

    preparation = _make_aware(
        donation.preparation_datetime
    )

    deadline = _make_aware(
        donation.safe_consumption_deadline
    )

    if deadline <= preparation:
        raise ValueError(
            "Safe consumption deadline must be after "
            "the preparation time."
        )

    save_donations()

    return donation


def cancel_donation(
    donation_id: str,
    donor_id: str,
) -> Donation:

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

    if donation.donor_id != donor_id:
        raise ValueError(
            "You are not authorized to cancel this donation."
        )

    if donation.status not in {
        AVAILABLE,
        PARTIALLY_RESERVED,
    }:
        raise ValueError(
            "This donation cannot be cancelled in its current status."
        )

    donation.status = CANCELLED

    save_donations()

    return donation


def get_remaining_quantity(
    donation: Donation,
) -> int:

    return max(
        donation.quantity
        - donation.reserved_quantity,
        0,
    )


def reserve_quantity(
    donation: Donation,
    quantity: int,
):
    """
    Reserve quantity on a donation.

    The caller is responsible for persisting the change.
    """

    if quantity <= 0:
        raise ValueError(
            "Reservation quantity must be greater than zero."
        )

    remaining = get_remaining_quantity(
        donation
    )

    if quantity > remaining:
        raise ValueError(
            f"Only {remaining} {donation.unit} remaining."
        )

    donation.reserved_quantity += quantity

    remaining_after_reservation = (
        get_remaining_quantity(
            donation
        )
    )

    if remaining_after_reservation == 0:
        donation.status = RESERVED
    else:
        donation.status = PARTIALLY_RESERVED


def release_quantity(
    donation: Donation,
    quantity: int,
):
    """
    Release previously reserved quantity.

    The caller is responsible for persisting the change.
    """

    if quantity <= 0:
        raise ValueError(
            "Release quantity must be greater than zero."
        )

    if quantity > donation.reserved_quantity:
        raise ValueError(
            "Cannot release more quantity than currently reserved."
        )

    donation.reserved_quantity -= quantity

    if donation.reserved_quantity == 0:
        donation.status = AVAILABLE
    else:
        donation.status = PARTIALLY_RESERVED


def complete_donation(
    donation: Donation,
):
    donation.status = COMPLETED

    save_donations()