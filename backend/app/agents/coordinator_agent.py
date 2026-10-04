from typing import Any

from app.services.groq_service import GroqService


class CoordinatorAgent:
    """
    AI agent responsible for coordinating and summarizing
    the current donation workflow.

    The agent provides explanations and next-action suggestions.
    It does not change any backend state.
    """

    def __init__(self):
        self.groq = GroqService()

    def coordinate(
        self,
        donation: dict[str, Any],
        request: dict[str, Any],
        organization: dict[str, Any],
        donor: dict[str, Any],
        workflow_facts: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a workflow summary and suggested next action.
        """

        system_prompt = """
You are the Coordinator Agent for a food donation platform.

Your job is to summarize the current donation workflow and
identify the next appropriate action based ONLY on verified
backend information.

IMPORTANT RULES:

1. Never invent information.
2. Never change donation status.
3. Never change request status.
4. Never claim that an action has happened when it has not.
5. Never approve or reject a request.
6. Never schedule a pickup.
7. Never certify food safety.
8. Use only the information supplied by the backend.
9. The next_action must describe an action that still needs
   to be performed if the workflow is incomplete.
10. If the workflow is completed, clearly state that it is complete.
11. Return ONLY valid JSON.
12. Do not wrap the JSON in markdown.

Return exactly:

{
    "title": "",
    "summary": "",
    "next_action": "",
    "notification": ""
}
"""

        user_prompt = f"""
Coordinate the following food donation workflow.

DONATION:

{donation}


REQUEST:

{request}


ORGANIZATION:

{organization}


DONOR:

{donor}


VERIFIED WORKFLOW FACTS:

{workflow_facts}
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
                "Invalid Coordinator Agent response."
            )

        title = result.get(
            "title",
            "",
        )

        summary = result.get(
            "summary",
            "",
        )

        next_action = result.get(
            "next_action",
            "",
        )

        notification = result.get(
            "notification",
            "",
        )

        if not isinstance(title, str):
            title = ""

        if not isinstance(summary, str):
            summary = ""

        if not isinstance(next_action, str):
            next_action = ""

        if not isinstance(notification, str):
            notification = ""

        return {
            "title": title,
            "summary": summary,
            "next_action": next_action,
            "notification": notification,
        }