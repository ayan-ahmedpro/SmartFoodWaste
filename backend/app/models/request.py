from datetime import datetime

from pydantic import BaseModel


class DonationRequest(BaseModel):
    id: str

    donation_id: str
    organization_id: str

    requested_quantity: int
    collection_time: str
    message: str = ""

    status: str

    created_at: datetime