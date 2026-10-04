from typing import Any

from app.services.groq_service import GroqService


class FoodInventoryAgent:
    """
    AI agent responsible for analyzing food donation information.

    The agent only analyzes information supplied by the donor.
    It must never invent facts or certify food as safe.
    """

    def __init__(self):
        self.groq = GroqService()

    def analyze(
        self,
        food_name: str,
        category: str,
        quantity: int,
        unit: str,
        preparation_datetime: str,
        safe_consumption_deadline: str,
        storage_instructions: str,
        dietary_information: str,
        description: str,
    ) -> dict[str, Any]:
        """
        Analyze donor-provided food information.
        """

        system_prompt = """
You are the Food Inventory Agent for a food donation platform.

Your job is to organize and summarize information provided by
the food donor.

STRICT RULES:

1. Never invent information.
2. Never change quantities.
3. Never change dates.
4. Never invent ingredients.
5. Never invent dietary properties.
6. Never assume an allergy-related property.
7. Never claim that food is medically or legally safe.
8. Never certify food as safe to consume.
9. If information is missing, explicitly report it.
10. Use only information supplied in the user prompt.
11. Return ONLY valid JSON.
12. Do not wrap the JSON in markdown.

Return exactly this structure:

{
    "summary": "short summary",
    "food_category": "category",
    "important_information": [],
    "missing_information": [],
    "dietary_tags": []
}
"""

        user_prompt = f"""
Analyze this food donation:

Food name:
{food_name}

Category:
{category}

Quantity:
{quantity}

Unit:
{unit}

Preparation date/time:
{preparation_datetime}

Safe consumption deadline provided by donor:
{safe_consumption_deadline}

Storage instructions:
{storage_instructions}

Dietary information:
{dietary_information}

Description:
{description}
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
                "Invalid Food Inventory Agent response."
            )

        summary = result.get(
            "summary",
            "",
        )

        food_category = result.get(
            "food_category",
            "",
        )

        important_information = result.get(
            "important_information",
            [],
        )

        missing_information = result.get(
            "missing_information",
            [],
        )

        dietary_tags = result.get(
            "dietary_tags",
            [],
        )

        if not isinstance(summary, str):
            summary = ""

        if not isinstance(food_category, str):
            food_category = ""

        if not isinstance(
            important_information,
            list,
        ):
            important_information = []

        if not isinstance(
            missing_information,
            list,
        ):
            missing_information = []

        if not isinstance(
            dietary_tags,
            list,
        ):
            dietary_tags = []

        return {
            "summary": summary,
            "food_category": food_category,
            "important_information": [
                str(item)
                for item in important_information
            ],
            "missing_information": [
                str(item)
                for item in missing_information
            ],
            "dietary_tags": [
                str(item)
                for item in dietary_tags
            ],
        }