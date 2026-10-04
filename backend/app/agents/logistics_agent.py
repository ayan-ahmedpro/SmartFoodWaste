from typing import Any

from app.services.groq_service import GroqService


class LogisticsAgent:
    """
    AI agent responsible for suggesting logistics and
    collection guidance for a food donation.

    The agent only suggests. It does not confirm,
    schedule, or execute a pickup.
    """

    def __init__(self):
        self.groq = GroqService()

    def suggest_collection(
        self,
        donation: dict[str, Any],
        organization: dict[str, Any],
        collection_information: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate collection suggestions using only
        information supplied by the backend.
        """

        system_prompt = """
You are the Logistics Agent for a food donation platform.

Your job is to provide a practical collection suggestion
for a food donation.

IMPORTANT RULES:

1. Never invent information.
2. Never invent a pickup address.
3. Never invent a collection time.
4. Never calculate a new distance.
5. Never claim that a pickup has been scheduled.
6. Never claim that a collection has been confirmed.
7. Never change donation or request status.
8. Use only information provided by the backend.
9. Clearly identify suggestions as suggestions.
10. If information is missing, mention it in notes.
11. Return ONLY valid JSON.
12. Do not wrap the JSON in markdown.

Return exactly:

{
    "suggested_collection_time": "",
    "pickup_instructions": [],
    "notes": [],
    "summary": ""
}
"""

        user_prompt = f"""
Create a collection suggestion using the following information.

DONATION:

Food name:
{donation.get("food_name", "")}

Category:
{donation.get("category", "")}

Quantity:
{donation.get("quantity", "")}

Unit:
{donation.get("unit", "")}

Pickup address:
{donation.get("pickup_address", "")}

Preparation date/time:
{donation.get("preparation_datetime", "")}

Safe consumption deadline:
{donation.get("safe_consumption_deadline", "")}

Storage instructions:
{donation.get("storage_instructions", "")}

Dietary information:
{donation.get("dietary_information", "")}


ORGANIZATION:

Organization name:
{organization.get("name", "")}

Organization information:
{organization.get("description", "")}


VERIFIED COLLECTION INFORMATION:

{collection_information}
"""

        result = self.groq.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return self._validate_result(result)

    def _validate_result(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate and normalize the AI response.
        """

        if not isinstance(result, dict):
            raise ValueError(
                "Invalid Logistics Agent response."
            )

        suggested_collection_time = result.get(
            "suggested_collection_time",
            "",
        )

        pickup_instructions = result.get(
            "pickup_instructions",
            [],
        )

        notes = result.get(
            "notes",
            [],
        )

        summary = result.get(
            "summary",
            "",
        )

        if not isinstance(
            suggested_collection_time,
            str,
        ):
            suggested_collection_time = ""

        if not isinstance(
            pickup_instructions,
            list,
        ):
            pickup_instructions = []

        if not isinstance(
            notes,
            list,
        ):
            notes = []

        if not isinstance(
            summary,
            str,
        ):
            summary = ""

        return {
            "suggested_collection_time": (
                suggested_collection_time
            ),
            "pickup_instructions": [
                str(item)
                for item in pickup_instructions
            ],
            "notes": [
                str(item)
                for item in notes
            ],
            "summary": summary,
        }