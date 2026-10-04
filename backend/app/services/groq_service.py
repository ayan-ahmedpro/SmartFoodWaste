import json
from typing import Any

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL


class GroqService:
    """
    Central service for communicating with the Groq API.

    All AI agents can use this service instead of creating
    their own Groq client.
    """

    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not configured. "
                "Please add it to backend/.env."
            )

        self.client = Groq(
            api_key=GROQ_API_KEY
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0,
    ) -> str:
        """
        Generate a text response from the configured Groq model.
        """

        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=temperature,
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "Groq returned an empty response."
            )

        return content.strip()

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """
        Generate and parse a JSON response.
        """

        content = self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0,
        )

        try:
            return json.loads(content)

        except json.JSONDecodeError:
            # Some models may wrap JSON in markdown fences.
            cleaned_content = content.strip()

            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[
                    len("```json"):
                ].strip()

            elif cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[
                    len("```"):
                ].strip()

            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[
                    :-len("```")
                ].strip()

            try:
                return json.loads(cleaned_content)

            except json.JSONDecodeError as error:
                raise ValueError(
                    "Groq returned an invalid JSON response."
                ) from error