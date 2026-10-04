from typing import Any

from app.data.store import (
    users,
    donations,
    requests,
    organization_profiles,
)
from app.services.donation_service import (
    get_remaining_quantity,
)
from app.services.request_service import (
    get_request_by_id,
)
from app.utils.distance import calculate_distance


class LogisticsService:
    """
    Prepares verified logistics information for AI assistance.

    This service performs deterministic calculations only.

    The AI is not allowed to:
    - invent addresses
    - invent distances
    - invent collection times
    - schedule collections
    - change request status
    - change donation status
    """

    @staticmethod
    def _get_donation(
        donation_id: str,
    ):
        return next(
            (
                donation
                for donation in donations
                if donation.id == donation_id
            ),
            None,
        )

    @staticmethod
    def _get_organization(
        organization_id: str,
    ):
        return next(
            (
                user
                for user in users
                if user.id == organization_id
                and user.role == "organization"
            ),
            None,
        )

    @staticmethod
    def _get_organization_profile(
        organization_id: str,
    ):
        return next(
            (
                profile
                for profile in organization_profiles
                if profile.user_id == organization_id
            ),
            None,
        )

    @staticmethod
    def _calculate_distance(
        donation,
        organization_profile,
    ) -> float | None:

        if organization_profile is None:
            return None

        donor_latitude = getattr(
            donation,
            "latitude",
            None,
        )

        donor_longitude = getattr(
            donation,
            "longitude",
            None,
        )

        organization_latitude = getattr(
            organization_profile,
            "latitude",
            None,
        )

        organization_longitude = getattr(
            organization_profile,
            "longitude",
            None,
        )

        if None in (
            donor_latitude,
            donor_longitude,
            organization_latitude,
            organization_longitude,
        ):
            return None

        try:
            return calculate_distance(
                float(donor_latitude),
                float(donor_longitude),
                float(organization_latitude),
                float(organization_longitude),
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _serialize_donation(
        donation,
    ) -> dict[str, Any]:

        return {
            "id": donation.id,
            "food_name": donation.food_name,
            "category": donation.category,
            "quantity": donation.quantity,
            "remaining_quantity": get_remaining_quantity(
                donation
            ),
            "unit": donation.unit,
            "pickup_address": donation.pickup_address,
            "latitude": getattr(
                donation,
                "latitude",
                None,
            ),
            "longitude": getattr(
                donation,
                "longitude",
                None,
            ),
            "safe_consumption_deadline": (
                donation.safe_consumption_deadline
            ),
            "storage_instructions": (
                donation.storage_instructions
            ),
            "dietary_information": (
                donation.dietary_information
            ),
            "status": donation.status,
        }

    @staticmethod
    def _serialize_organization(
        organization,
        profile,
    ) -> dict[str, Any]:

        return {
            "id": organization.id,
            "name": organization.name,
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

    @staticmethod
    def _serialize_request(
        request,
    ) -> dict[str, Any]:

        return {
            "id": request.id,
            "donation_id": request.donation_id,
            "organization_id": request.organization_id,
            "requested_quantity": (
                request.requested_quantity
            ),
            "collection_time": (
                request.collection_time
            ),
            "message": request.message,
            "status": request.status,
            "created_at": request.created_at,
        }

    @classmethod
    def get_collection_information(
        cls,
        request_id: str,
        organization_id: str,
    ) -> dict[str, Any]:

        request = get_request_by_id(
            request_id
        )

        if request is None:
            raise ValueError(
                "Request not found."
            )

        if request.organization_id != organization_id:
            raise ValueError(
                "You are not authorized to access "
                "this collection information."
            )

        donation = cls._get_donation(
            request.donation_id
        )

        if donation is None:
            raise ValueError(
                "Donation not found."
            )

        organization = cls._get_organization(
            organization_id
        )

        if organization is None:
            raise ValueError(
                "Organization not found."
            )

        profile = cls._get_organization_profile(
            organization_id
        )

        distance_km = cls._calculate_distance(
            donation,
            profile,
        )

        return {
            "request": cls._serialize_request(
                request
            ),
            "donation": cls._serialize_donation(
                donation
            ),
            "organization": cls._serialize_organization(
                organization,
                profile,
            ),
            "logistics_facts": {
                "collection_time": (
                    request.collection_time
                ),
                "requested_quantity": (
                    request.requested_quantity
                ),
                "unit": donation.unit,
                "pickup_address": (
                    donation.pickup_address
                ),
                "distance_km": distance_km,
                "donation_status": (
                    donation.status
                ),
                "request_status": (
                    request.status
                ),
                "remaining_quantity": (
                    get_remaining_quantity(
                        donation
                    )
                ),
            },
        }


logistics_service = LogisticsService()