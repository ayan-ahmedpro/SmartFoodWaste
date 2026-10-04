from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str
    email: str
    password_hash: str
    role: str
    status: str = "ACTIVE"