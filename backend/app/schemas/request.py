from pydantic import BaseModel, Field


class DonationRequestCreate(BaseModel):
    requested_quantity: int = Field(gt=0)
    collection_time: str
    message: str = ""