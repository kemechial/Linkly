from pydantic import BaseModel, HttpUrl
from datetime import datetime

class LinkCreate(BaseModel):
    target_url: HttpUrl

class LinkRead(BaseModel):
    id: int
    short_key: str
    target_url: HttpUrl
    created_at: datetime
    clicks: int

    class Config:
        orm_mode = True

class LinkStats(BaseModel):
    short_key: str
    clicks: int