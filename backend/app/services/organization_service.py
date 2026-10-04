from typing import Any

from app.data.store import (
    organization_profiles,
    save_organization_profiles,
)
from app.models.organization import OrganizationProfile


class OrganizationService:
    """
    Handles organization-specific profile information.

    Organization account information remains in users.json.
    Organization matching preferences are stored separately
    in organization_profiles.json.
    """

    @staticmethod
    def get_profile(
        user_id: str,
    ) -> OrganizationProfile | None:
        """
        Return the organization profile for a user.
        """

        return next(
            (
                profile
                for profile in organization_profiles
                if profile.user_id == user_id
            ),
            None,
        )

    @staticmethod
    def get_or_create_profile(
        user_id: str,
    ) -> OrganizationProfile:
        """
        Return an existing organization profile.

        If one does not exist yet, create a default profile.
        """

        profile = OrganizationService.get_profile(
            user_id
        )

        if profile is not None:
            return profile

        profile = OrganizationProfile(
            user_id=user_id,
        )

        organization_profiles.append(
            profile
        )

        save_organization_profiles()

        return profile

    @staticmethod
    def update_profile(
        user_id: str,
        data: dict[str, Any],
    ) -> OrganizationProfile:
        """
        Create or update an organization's matching profile.
        """

        profile = OrganizationService.get_or_create_profile(
            user_id
        )

        # -----------------------------------------------------------
        # Accepted food categories
        # -----------------------------------------------------------

        if "accepted_food_categories" in data:

            categories = data.get(
                "accepted_food_categories"
            )

            if categories is None:
                categories = []

            if not isinstance(categories, list):
                raise ValueError(
                    "accepted_food_categories must be a list."
                )

            profile.accepted_food_categories = [
                str(category).strip()
                for category in categories
                if str(category).strip()
            ]

        # -----------------------------------------------------------
        # Dietary requirements
        # -----------------------------------------------------------

        if "dietary_requirements" in data:

            requirements = data.get(
                "dietary_requirements"
            )

            if requirements is None:
                requirements = []

            if not isinstance(requirements, list):
                raise ValueError(
                    "dietary_requirements must be a list."
                )

            profile.dietary_requirements = [
                str(requirement).strip()
                for requirement in requirements
                if str(requirement).strip()
            ]

        # -----------------------------------------------------------
        # Minimum quantity
        # -----------------------------------------------------------

        if "minimum_quantity" in data:

            minimum_quantity = data.get(
                "minimum_quantity"
            )

            try:
                minimum_quantity = int(
                    minimum_quantity
                )
            except (
                TypeError,
                ValueError,
            ) as error:
                raise ValueError(
                    "minimum_quantity must be a whole number."
                ) from error

            if minimum_quantity < 0:
                raise ValueError(
                    "minimum_quantity cannot be negative."
                )

            profile.minimum_quantity = (
                minimum_quantity
            )

        # -----------------------------------------------------------
        # Latitude
        # -----------------------------------------------------------

        if "latitude" in data:

            latitude = data.get(
                "latitude"
            )

            if latitude in (
                None,
                "",
            ):
                profile.latitude = None

            else:
                try:
                    latitude = float(
                        latitude
                    )
                except (
                    TypeError,
                    ValueError,
                ) as error:
                    raise ValueError(
                        "latitude must be a number."
                    ) from error

                if not -90 <= latitude <= 90:
                    raise ValueError(
                        "latitude must be between -90 and 90."
                    )

                profile.latitude = latitude

        # -----------------------------------------------------------
        # Longitude
        # -----------------------------------------------------------

        if "longitude" in data:

            longitude = data.get(
                "longitude"
            )

            if longitude in (
                None,
                "",
            ):
                profile.longitude = None

            else:
                try:
                    longitude = float(
                        longitude
                    )
                except (
                    TypeError,
                    ValueError,
                ) as error:
                    raise ValueError(
                        "longitude must be a number."
                    ) from error

                if not -180 <= longitude <= 180:
                    raise ValueError(
                        "longitude must be between -180 and 180."
                    )

                profile.longitude = longitude

        # -----------------------------------------------------------
        # Persist changes
        # -----------------------------------------------------------

        save_organization_profiles()

        return profile


organization_service = OrganizationService()