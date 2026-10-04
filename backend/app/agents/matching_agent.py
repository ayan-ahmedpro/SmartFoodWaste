from crewai import Agent


def create_matching_agent(llm) -> Agent:
    """
    Create the CrewAI matching agent.

    The LLM instance is passed from the central CrewAI
    orchestrator, so this module does not import anything
    from crew.py.
    """

    return Agent(
        role="Donation Matching Analyst",
        goal=(
            "Explain why a food donation may match an organization "
            "using only verified matching facts supplied by the backend."
        ),
        backstory=(
            "You analyze food donation and organization matching information. "
            "The backend has already calculated the actual matching facts. "
            "You must never invent distance, quantity, food preferences, "
            "location, availability, or organization requirements. "
            "You do not approve, reject, reserve, or modify donations."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )