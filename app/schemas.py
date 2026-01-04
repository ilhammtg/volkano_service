from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

VALID_LEVELS = {"Normal", "Waspada", "Siaga", "Awas"}

def normalize_level(level: str) -> str:
    x = level.strip().lower()
    if x in {"normal", "waspada", "siaga", "awas"}:
        return x.capitalize()
    return level.strip()

class VolcanoCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    province: Optional[str] = Field(None, max_length=80)
    latitude: float
    longitude: float
    level: str
    source: str = "PVMBG/MAGMA"
    status_text: Optional[str] = None
    observed_at: datetime 
    # observed_at is mandatory in new SQL schema: NOT NULL

class VolcanoOut(BaseModel):
    id: UUID
    name: str
    province: Optional[str]
    latitude: float
    longitude: float
    level: str
    source: str
    status_text: Optional[str] = None
    observed_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
