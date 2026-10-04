from datetime import datetime

from pydantic import BaseModel, Field


class DonationCreate(BaseModel):
    food_name: str
    category: str
    quantity: int = Field(gt=0)
    unit: str

    preparation_datetime: datetime
    safe_consumption_deadline: datetime

    pickup_address: str

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    storage_instructions: str = ""
    dietary_information: str = ""
    description: str = ""


class DonationUpdate(BaseModel):
    food_name: str | None = None
    category: str | None = None
    quantity: int | None = Field(
        default=None,
        gt=0,
    )
    unit: str | None = None

    preparation_datetime: datetime | None = None
    safe_consumption_deadline: datetime | None = None

    pickup_address: str | None = None

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    storage_instructions: str | None = None
    dietary_information: str | None = None
    description: str | None = None