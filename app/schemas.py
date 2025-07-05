from pydantic import BaseModel, HttpUrl, EmailStr, ConfigDict
from datetime import datetime

class LinkCreate(BaseModel):
    target_url: HttpUrl

class LinkRead(BaseModel):
    id: int
    short_key: str
    target_url: HttpUrl
    created_at: datetime
    clicks: int

    model_config = ConfigDict(from_attributes=True)

class LinkStats(BaseModel):
    short_key: str
    clicks: int


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str