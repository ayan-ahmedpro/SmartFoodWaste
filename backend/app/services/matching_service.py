from typing import Any

from app.services.ai_service import ai_service
from app.utils.distance import calculate_distance


class MatchingService:
    """
    Handles deterministic donation-to-organization matching.

    The backend calculates the actual matching facts.
    AI is only used to explain those facts in natural language.
    """

    # ---------------------------------------------------------
    # BASIC HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _normalize(value: Any) -> str:
        """
        Convert a value into a normalized lowercase string.
        """
        if value is None:
            return ""

        return str(value).strip().lower()

    @staticmethod
    def _list_from_value(value: Any) -> list[str]:
        """
        Convert common JSON values into a list of strings.
        """

        if value is None:
            return []

        if isinstance(value, list):
            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

        if isinstance(value, str):

            if not value.strip():
                return []

            return [
                item.strip()
                for item in value.split(",")
                if item.strip()
            ]

        return [str(value).strip()]

    # ---------------------------------------------------------
    # FOOD CATEGORY MATCH
    # ---------------------------------------------------------

    @classmethod
    def _category_matches(
        cls,
        donation: dict[str, Any],
        organization: dict[str, Any],
    ) -> bool:

        donation_category = cls._normalize(
            donation.get("category")
        )

        if not donation_category:
            return True

        accepted_categories = cls._list_from_value(
            organization.get("accepted_food_categories")
        )

        if not accepted_categories:
            return True

        normalized_categories = [
            cls._normalize(category)
            for category in accepted_categories
        ]

        return (
            donation_category
            in normalized_categories
        )

    # ---------------------------------------------------------
    # DIETARY MATCH
    # ---------------------------------------------------------

    @classmethod
    def _dietary_match(
        cls,
        donation: dict[str, Any],
        organization: dict[str, Any],
    ) -> bool:

        donation_dietary = cls._list_from_value(
            donation.get("dietary_information")
        )

        organization_requirements = cls._list_from_value(
            organization.get("dietary_requirements")
        )

        if not organization_requirements:
            return True

        if not donation_dietary:
            return False

        donation_values = {
            cls._normalize(value)
            for value in donation_dietary
        }

        required_values = {
            cls._normalize(value)
            for value in organization_requirements
        }

        return bool(
            donation_values.intersection(
                required_values
            )
        )

    # ---------------------------------------------------------
    # QUANTITY MATCH
    # ---------------------------------------------------------

    @staticmethod
    def _quantity_match(
        donation: dict[str, Any],
        organization: dict[str, Any],
    ) -> bool:

        donation_quantity = float(
            donation.get("remaining_quantity", 0)
            or donation.get("quantity", 0)
            or 0
        )

        minimum_quantity = float(
            organization.get(
                "minimum_quantity",
                0,
            )
            or 0
        )

        if minimum_quantity <= 0:
            return True

        return (
            donation_quantity
            >= minimum_quantity
        )

    # ---------------------------------------------------------
    # DISTANCE
    # ---------------------------------------------------------

    @staticmethod
    def _calculate_distance(
        donation: dict[str, Any],
        organization: dict[str, Any],
    ):

        donor_lat = donation.get(
            "latitude"
        )
        donor_lon = donation.get(
            "longitude"
        )

        organization_lat = organization.get(
            "latitude"
        )
        organization_lon = organization.get(
            "longitude"
        )

        if None in (
            donor_lat,
            donor_lon,
            organization_lat,
            organization_lon,
        ):
            return None

        try:
            return calculate_distance(
                float(donor_lat),
                float(donor_lon),
                float(organization_lat),
                float(organization_lon),
            )

        except (
            ValueError,
            TypeError,
        ):
            return None

    # ---------------------------------------------------------
    # MATCH SINGLE ORGANIZATION
    # ---------------------------------------------------------

    @classmethod
    def calculate_match(
        cls,
        donation: dict[str, Any],
        organization: dict[str, Any],
    ) -> dict[str, Any]:

        category_match = cls._category_matches(
            donation,
            organization,
        )

        dietary_match = cls._dietary_match(
            donation,
            organization,
        )

        quantity_match = cls._quantity_match(
            donation,
            organization,
        )

        distance_km = cls._calculate_distance(
            donation,
            organization,
        )

        matching_facts = {
            "category_match": category_match,
            "dietary_match": dietary_match,
            "quantity_match": quantity_match,
            "distance_km": distance_km,
        }

        matches = [
            category_match,
            dietary_match,
            quantity_match,
        ]

        matched_count = sum(
            1
            for match in matches
            if match
        )

        if matched_count == len(matches):
            match_status = "MATCHED"

        elif matched_count > 0:
            match_status = "PARTIALLY_MATCHED"

        else:
            match_status = "NOT_MATCHED"

        matching_facts["matched_count"] = (
            matched_count
        )

        matching_facts["total_checks"] = (
            len(matches)
        )

        matching_facts["match_status"] = (
            match_status
        )

        return matching_facts

    # ---------------------------------------------------------
    # AI EXPLANATION
    # ---------------------------------------------------------

    @classmethod
    def explain_match(
        cls,
        donation: dict[str, Any],
        organization: dict[str, Any],
    ) -> dict[str, Any]:

        matching_facts = cls.calculate_match(
            donation,
            organization,
        )

        ai_result = ai_service.explain_match(
            donation=donation,
            organization=organization,
            matching_facts=matching_facts,
        )

        return {
            "success": True,
            "matching_facts": matching_facts,
            "ai": ai_result,
        }

    # ---------------------------------------------------------
    # FIND ALL MATCHES
    # ---------------------------------------------------------

    @classmethod
    def find_matches(
        cls,
        donation: dict[str, Any],
        organizations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        results = []

        for organization in organizations:

            matching_facts = cls.calculate_match(
                donation,
                organization,
            )

            results.append(
                {
                    "organization": organization,
                    "matching_facts": matching_facts,
                }
            )

        return results


matching_service = MatchingService()