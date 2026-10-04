import json
from typing import Any

from app.agents.crew import crew


class AIService:
    """
    Application-level service for AI operations.

    This layer keeps CrewAI orchestration away from API routes
    and converts CrewAI results into clean JSON-friendly data.
    """

    @staticmethod
    def _parse_json_result(
        result: Any,
    ) -> dict[str, Any]:

        if result is None:
            raise ValueError(
                "AI returned an empty result."
            )

        raw = getattr(
            result,
            "raw",
            None,
        )

        if raw is None:
            raw = str(result)

        raw = str(raw).strip()

        if raw.startswith("```json"):
            raw = raw[
                len("```json"):
            ].strip()

        elif raw.startswith("```"):
            raw = raw[
                len("```"):
            ].strip()

        if raw.endswith("```"):
            raw = raw[
                :-3
            ].strip()

        try:
            parsed = json.loads(raw)

        except json.JSONDecodeError as error:
            raise ValueError(
                "AI returned invalid JSON."
            ) from error

        if not isinstance(parsed, dict):
            raise ValueError(
                "AI returned JSON in an unexpected format."
            )

        return parsed

    @staticmethod
    def _validate_food_analysis(
        data: dict[str, Any],
    ) -> dict[str, Any]:

        important_information = data.get(
            "important_information",
            [],
        )

        missing_information = data.get(
            "missing_information",
            [],
        )

        dietary_tags = data.get(
            "dietary_tags",
            [],
        )

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
            "summary": str(
                data.get(
                    "summary",
                    "",
                )
            ),
            "food_category": str(
                data.get(
                    "food_category",
                    "",
                )
            ),
            "important_information": (
                important_information
            ),
            "missing_information": (
                missing_information
            ),
            "dietary_tags": dietary_tags,
        }

    @staticmethod
    def analyze_food(
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

        try:
            result = crew.analyze_food(
                food_name=food_name,
                category=category,
                quantity=quantity,
                unit=unit,
                preparation_datetime=(
                    preparation_datetime
                ),
                safe_consumption_deadline=(
                    safe_consumption_deadline
                ),
                storage_instructions=(
                    storage_instructions
                ),
                dietary_information=(
                    dietary_information
                ),
                description=description,
            )

            parsed_data = (
                AIService._parse_json_result(
                    result
                )
            )

            validated_data = (
                AIService._validate_food_analysis(
                    parsed_data
                )
            )

            return {
                "success": True,
                "ai_available": True,
                "data": validated_data,
            }

        except Exception:
            return {
                "success": False,
                "ai_available": False,
                "message": (
                    "Food analysis is temporarily "
                    "unavailable. The donation "
                    "information can still be managed "
                    "using the information provided "
                    "by the donor."
                ),
                "data": {
                    "summary": (
                        f"{food_name} donation "
                        f"containing "
                        f"{quantity} {unit}."
                    ),
                    "food_category": category,
                    "important_information": [
                        {
                            "label": "Quantity",
                            "value": (
                                f"{quantity} "
                                f"{unit}"
                            ),
                        }
                    ],
                    "missing_information": [
                        "AI analysis unavailable."
                    ],
                    "dietary_tags": [],
                },
            }

    @staticmethod
    def explain_match(
        donation: dict[str, Any],
        organization: dict[str, Any],
        matching_facts: dict[str, Any],
    ) -> dict[str, Any]:

        try:
            result = crew.explain_match(
                donation=donation,
                organization=organization,
                matching_facts=matching_facts,
            )

            raw = getattr(
                result,
                "raw",
                result,
            )

            return {
                "success": True,
                "ai_available": True,
                "data": {
                    "raw": str(raw),
                },
            }

        except Exception:
            return {
                "success": False,
                "ai_available": False,
                "message": (
                    "AI match explanation is "
                    "temporarily unavailable."
                ),
                "data": {
                    "organization_id": str(
                        organization.get(
                            "id",
                            "",
                        )
                    ),
                    "reason": (
                        "This organization passed "
                        "the backend matching checks."
                    ),
                    "strengths": [],
                    "considerations": [
                        "AI explanation unavailable."
                    ],
                },
            }

    @staticmethod
    def _validate_logistics_suggestion(
        data: dict[str, Any],
    ) -> dict[str, Any]:

        collection_considerations = data.get(
            "collection_considerations",
            [],
        )

        timing_considerations = data.get(
            "timing_considerations",
            [],
        )

        practical_notes = data.get(
            "practical_notes",
            [],
        )

        if not isinstance(
            collection_considerations,
            list,
        ):
            collection_considerations = []

        if not isinstance(
            timing_considerations,
            list,
        ):
            timing_considerations = []

        if not isinstance(
            practical_notes,
            list,
        ):
            practical_notes = []

        return {
            "summary": str(
                data.get(
                    "summary",
                    "",
                )
            ),
            "collection_considerations": [
                str(item)
                for item in collection_considerations
            ],
            "timing_considerations": [
                str(item)
                for item in timing_considerations
            ],
            "practical_notes": [
                str(item)
                for item in practical_notes
            ],
        }

    @staticmethod
    def suggest_collection(
        donation: dict[str, Any],
        organization: dict[str, Any],
        collection_information: dict[str, Any],
    ) -> dict[str, Any]:

        try:
            result = crew.suggest_collection(
                donation=donation,
                organization=organization,
                collection_information=(
                    collection_information
                ),
            )

            parsed_data = (
                AIService._parse_json_result(
                    result
                )
            )

            validated_data = (
                AIService._validate_logistics_suggestion(
                    parsed_data
                )
            )

            return {
                "success": True,
                "ai_available": True,
                "data": validated_data,
            }

        except Exception:
            return {
                "success": False,
                "ai_available": False,
                "message": (
                    "AI logistics suggestions "
                    "are temporarily unavailable."
                ),
                "data": {
                    "summary": (
                        "Collection should follow "
                        "the confirmed information "
                        "provided by the donor and "
                        "organization."
                    ),
                    "collection_considerations": [
                        (
                            "Use the pickup address "
                            "provided with the donation."
                        ),
                        (
                            "Follow the collection "
                            "time provided in the request."
                        ),
                    ],
                    "timing_considerations": [
                        (
                            "Confirm the collection "
                            "time between the donor "
                            "and organization."
                        ),
                    ],
                    "practical_notes": [
                        (
                            "Do not change the "
                            "request or donation "
                            "status through AI."
                        ),
                        (
                            "Follow the food storage "
                            "instructions provided "
                            "by the donor."
                        ),
                    ],
                },
            }

    @staticmethod
    def _validate_coordinator_result(
        data: dict[str, Any],
        donation: dict[str, Any],
        request: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate and normalize the Coordinator AI response.

        The AI output is treated as explanatory text only.
        It cannot change the actual workflow facts.
        """

        important_information = data.get(
            "important_information",
            [],
        )

        if not isinstance(
            important_information,
            list,
        ):
            important_information = []

        return {
            "title": str(
                data.get(
                    "title",
                    "Donation Workflow Update",
                )
            ),
            "summary": str(
                data.get(
                    "summary",
                    "",
                )
            ),
            "current_status": str(
                data.get(
                    "current_status",
                    request.get(
                        "status",
                        "",
                    ),
                )
            ),
            "next_action": str(
                data.get(
                    "next_action",
                    "Follow the next action required "
                    "by the current request status.",
                )
            ),
            "important_information": [
                str(item)
                for item in important_information
            ],
        }

    @staticmethod
    def coordinate(
        donation: dict[str, Any],
        request: dict[str, Any],
        organization: dict[str, Any],
        donor: dict[str, Any],
        workflow_facts: dict[str, Any],
    ) -> dict[str, Any]:

        try:
            result = crew.coordinate(
                donation=donation,
                request=request,
                organization=organization,
                donor=donor,
                workflow_facts=workflow_facts,
            )

            parsed_data = (
                AIService._parse_json_result(
                    result
                )
            )

            validated_data = (
                AIService._validate_coordinator_result(
                    parsed_data,
                    donation,
                    request,
                )
            )

            return {
                "success": True,
                "ai_available": True,
                "data": validated_data,
            }

        except Exception:
            return {
                "success": False,
                "ai_available": False,
                "message": (
                    "AI coordination summary "
                    "is temporarily unavailable."
                ),
                "data": {
                    "title": (
                        "Donation Workflow Update"
                    ),
                    "summary": (
                        f"Donation "
                        f"'{donation.get('food_name', '')}' "
                        f"currently has request status "
                        f"'{request.get('status', '')}'."
                    ),
                    "current_status": str(
                        request.get(
                            "status",
                            "",
                        )
                    ),
                    "next_action": (
                        "Follow the next action "
                        "required by the current "
                        "request status."
                    ),
                    "important_information": [
                        (
                            "The AI coordination "
                            "summary is unavailable."
                        ),
                        (
                            "Use the current request "
                            "and donation status shown "
                            "by the application."
                        ),
                    ],
                },
            }


ai_service = AIService()