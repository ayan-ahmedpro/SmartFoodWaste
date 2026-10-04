from pydantic import BaseModel, Field


class OrganizationProfile(BaseModel):
    """
    Organization-specific information used for
    donation matching and collection planning.
    """

    user_id: str

    accepted_food_categories: list[str] = Field(
        default_factory=list
    )

    dietary_requirements: list[str] = Field(
        default_factory=list
    )

    minimum_quantity: int = 0

    latitude: float | None = None

    longitude: float | None = None