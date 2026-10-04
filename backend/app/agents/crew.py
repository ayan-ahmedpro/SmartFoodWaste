from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM
from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.agents.matching_agent import create_matching_agent


class GroqCrewLLM(BaseLLM):
    """
    Custom CrewAI LLM implementation using the official Groq SDK.

    This avoids requiring LiteLLM and keeps Groq communication
    directly inside the application.
    """

    def __init__(self):
        super().__init__(
            model=GROQ_MODEL,
            temperature=0,
            provider="groq",
        )

        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not configured. "
                "Please add it to backend/.env."
            )

        self.client = Groq(
            api_key=GROQ_API_KEY
        )

    def call(
        self,
        messages: str | list[Any],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Any | None = None,
        from_agent: Any | None = None,
        response_model: Any | None = None,
    ) -> str | Any:

        if isinstance(messages, str):
            groq_messages = [
                {
                    "role": "user",
                    "content": messages,
                }
            ]

        else:
            groq_messages = []

            for message in messages:

                if isinstance(message, dict):
                    role = message.get(
                        "role",
                        "user",
                    )

                    content = message.get(
                        "content",
                        "",
                    )

                else:
                    role = getattr(
                        message,
                        "role",
                        "user",
                    )

                    content = getattr(
                        message,
                        "content",
                        "",
                    )

                groq_messages.append(
                    {
                        "role": role,
                        "content": content,
                    }
                )

        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=groq_messages,
            temperature=self.temperature or 0,
            max_tokens=(
                int(self.max_tokens)
                if self.max_tokens is not None
                else None
            ),
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "Groq returned an empty response."
            )

        return content.strip()


class CrewAIOrchestrator:
    """
    Central CrewAI orchestration layer.

    The application services call this class instead of
    interacting with CrewAI directly.
    """

    def __init__(self):

        self.llm = GroqCrewLLM()

        self.food_inventory_agent = Agent(
            role="Food Inventory Analyst",
            goal=(
                "Analyze donated food information accurately "
                "using only information supplied by the application."
            ),
            backstory=(
                "You analyze food donation information. "
                "You never invent missing facts. "
                "You never certify food safety."
            ),
            llm=self.llm,
            allow_delegation=False,
            verbose=False,
        )

        self.matching_agent = create_matching_agent(
            self.llm
        )

        self.logistics_agent = Agent(
            role="Food Collection Logistics Analyst",
            goal=(
                "Provide structured collection considerations "
                "using only verified logistics information "
                "supplied by the application."
            ),
            backstory=(
                "You analyze collection logistics for food "
                "donations. You only explain information "
                "provided by the backend. You never invent "
                "addresses, distances, quantities, times, "
                "or schedules. You never schedule collections "
                "and never certify food safety."
            ),
            llm=self.llm,
            allow_delegation=False,
            verbose=False,
        )

        self.coordinator_agent = Agent(
            role="Donation Workflow Coordinator",
            goal=(
                "Summarize the current donation workflow "
                "using verified backend information."
            ),
            backstory=(
                "You coordinate workflow information. "
                "You do not change statuses, approve requests, "
                "reject requests, schedule collections, "
                "or certify food safety."
            ),
            llm=self.llm,
            allow_delegation=False,
            verbose=False,
        )

    def analyze_food(
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
    ):

        food_information = f"""
Food Name: {food_name}
Category: {category}
Quantity: {quantity}
Unit: {unit}
Preparation Date and Time: {preparation_datetime}
Safe Consumption Deadline: {safe_consumption_deadline}
Storage Instructions: {storage_instructions}
Dietary Information: {dietary_information}
Description: {description}
"""

        task = Task(
            description=f"""
Analyze the following food donation information.

{food_information}

IMPORTANT RULES:

1. Use ONLY the information provided above.
2. Never invent ingredients.
3. Never invent allergens.
4. Never invent nutritional information.
5. Never invent preparation details.
6. Never invent storage requirements.
7. Never invent dates or times.
8. Never certify that the food is safe.
9. If information is missing, explicitly mention it.
10. Do not modify the supplied quantity.
11. Do not modify the supplied food category.
12. Do not change the donation status.

Return ONLY valid JSON.

The JSON must have exactly this structure:

{{
    "summary": "string",
    "food_category": "string",
    "important_information": [
        {{
            "label": "string",
            "value": "string"
        }}
    ],
    "missing_information": [
        "string"
    ],
    "dietary_tags": [
        "string"
    ]
}}

Do not use Markdown.
Do not use code fences.
Return JSON only.
""",
            expected_output=(
                "A valid JSON object containing "
                "summary, food_category, "
                "important_information, "
                "missing_information, and dietary_tags."
            ),
            agent=self.food_inventory_agent,
        )

        crew_instance = Crew(
            agents=[
                self.food_inventory_agent,
            ],
            tasks=[
                task,
            ],
            process=Process.sequential,
            verbose=False,
        )

        return crew_instance.kickoff()

    def explain_match(
        self,
        donation: dict[str, Any],
        organization: dict[str, Any],
        matching_facts: dict[str, Any],
    ):

        task = Task(
            description=f"""
Explain the potential match between this food donation
and organization.

DONATION:
{donation}

ORGANIZATION:
{organization}

BACKEND MATCHING FACTS:
{matching_facts}

IMPORTANT RULES:

1. Use only the supplied information.
2. Do not invent facts.
3. Do not invent distance.
4. Do not invent quantities.
5. Do not invent food preferences.
6. Do not invent organization requirements.
7. Do not approve or reject the match.
8. Do not reserve the donation.
9. The backend has already calculated the matching facts.
10. Your job is only to explain those facts clearly.

Provide a concise human-readable explanation.
""",
            expected_output=(
                "A concise explanation of the matching facts."
            ),
            agent=self.matching_agent,
        )

        crew_instance = Crew(
            agents=[
                self.matching_agent,
            ],
            tasks=[
                task,
            ],
            process=Process.sequential,
            verbose=False,
        )

        return crew_instance.kickoff()

    def suggest_collection(
        self,
        donation: dict[str, Any],
        organization: dict[str, Any],
        collection_information: dict[str, Any],
    ):

        task = Task(
            description=f"""
Analyze the following food donation collection
information.

DONATION:
{donation}

ORGANIZATION:
{organization}

VERIFIED COLLECTION INFORMATION:
{collection_information}

Your job is ONLY to explain the supplied logistics
information clearly.

IMPORTANT RULES:

1. Use ONLY the information supplied above.
2. Never invent an address.
3. Never invent a distance.
4. Never invent a quantity.
5. Never invent a collection time.
6. Never invent a schedule.
7. Never invent transportation details.
8. Never claim that a collection has been scheduled.
9. Never change the request status.
10. Never change the donation status.
11. Never approve or reject a request.
12. Never reserve or release food.
13. Never certify food safety.
14. Do not create facts that are not present
    in the supplied information.
15. If a logistics fact is missing, say that it
    is not provided.

Return ONLY valid JSON.

The JSON must have EXACTLY this structure:

{{
    "summary": "string",
    "collection_considerations": [
        "string"
    ],
    "timing_considerations": [
        "string"
    ],
    "practical_notes": [
        "string"
    ]
}}

Field rules:

summary:
A short explanation of the current collection situation.

collection_considerations:
List only practical considerations based on
the supplied pickup address, distance, quantity,
storage instructions, organization information,
and other verified facts.

timing_considerations:
Discuss only the supplied collection time,
safe consumption deadline, or other supplied
time information.

practical_notes:
Provide useful notes based only on supplied facts.
Do not invent instructions.

If information is missing, clearly state that
the information was not provided.

Do not use Markdown.
Do not use code fences.
Return JSON only.
""",
            expected_output=(
                "A valid JSON object containing "
                "summary, collection_considerations, "
                "timing_considerations, and "
                "practical_notes."
            ),
            agent=self.logistics_agent,
        )

        crew_instance = Crew(
            agents=[
                self.logistics_agent,
            ],
            tasks=[
                task,
            ],
            process=Process.sequential,
            verbose=False,
        )

        return crew_instance.kickoff()

    def coordinate(
        self,
        donation: dict[str, Any],
        request: dict[str, Any],
        organization: dict[str, Any],
        donor: dict[str, Any],
        workflow_facts: dict[str, Any],
    ):

        task = Task(
            description=f"""
Summarize the current food donation workflow.

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

Your job is ONLY to explain the current workflow
using the supplied information.

IMPORTANT RULES:

1. Use ONLY the supplied information.
2. Never invent facts.
3. Never change request status.
4. Never change donation status.
5. Never approve a request.
6. Never reject a request.
7. Never schedule a collection.
8. Never invent collection times.
9. Never invent quantities.
10. Never invent addresses.
11. Never invent donor information.
12. Never invent organization information.
13. Never reserve food.
14. Never release food.
15. Never certify food safety.
16. The current request status supplied by the
    backend is authoritative.
17. The current donation status supplied by the
    backend is authoritative.
18. Explain the next workflow action based only
    on the current supplied status.
19. If information is missing, explicitly say
    that it was not provided.

Return ONLY valid JSON.

The JSON must have EXACTLY this structure:

{{
    "title": "Donation Workflow Update",
    "summary": "string",
    "current_status": "string",
    "next_action": "string",
    "important_information": [
        "string"
    ]
}}

Field rules:

title:
A short title for the workflow update.

summary:
A concise explanation of the current donation
and request situation.

current_status:
Report the current request status supplied by
the backend. Do not invent or modify it.

next_action:
Explain the next action that should be considered
according to the current request status.

Do not perform the action.
Do not claim that the action has already happened
unless the supplied backend information confirms it.

important_information:
List important workflow facts directly supported
by the supplied donation, request, organization,
donor, and workflow information.

Do not use Markdown.
Do not use code fences.
Return JSON only.
""",
            expected_output=(
                "A valid JSON object containing "
                "title, summary, current_status, "
                "next_action, and important_information."
            ),
            agent=self.coordinator_agent,
        )

        crew_instance = Crew(
            agents=[
                self.coordinator_agent,
            ],
            tasks=[
                task,
            ],
            process=Process.sequential,
            verbose=False,
        )

        return crew_instance.kickoff()


crew = CrewAIOrchestrator()