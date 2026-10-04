from datetime import datetime

from pydantic import BaseModel


class Donation(BaseModel):
    id: str
    donor_id: str

    food_name: str
    category: str
    quantity: int
    reserved_quantity: int = 0
    unit: str

    preparation_datetime: datetime
    safe_consumption_deadline: datetime

    pickup_address: str

    latitude: float | None = None
    longitude: float | None = None

    storage_instructions: str
    dietary_information: str
    description: str

    status: str