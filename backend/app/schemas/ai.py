# backend/app/schemas/ai.py

from typing import Any

from pydantic import BaseModel, Field


class FoodAnalysisResponse(BaseModel):
    """
    Clean API response returned by the food analysis service.
    """

    success: bool
    ai_available: bool
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)