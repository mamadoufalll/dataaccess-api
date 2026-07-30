from pydantic import BaseModel, Field
from typing import Optional
from app.models.dataset import Classification, DatasetStatus
import datetime

class DatasetCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    classification: Classification = Classification.PUBLIC
    purpose: Optional[str] = None
    retention_days: int = Field(default=365, ge=1)
    contact: Optional[str] = Field(None, max_length=100)

class DatasetUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    classification: Optional[Classification] = None
    purpose: Optional[str] = None
    retention_days: Optional[int] = Field(None, ge=1)
    contact: Optional[str] = Field(None, max_length=100)

class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    classification: Classification
    purpose: Optional[str]
    retention_days: int
    contact: Optional[str]
    status: DatasetStatus
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime]
    owner_id: int

    model_config = {"from_attributes": True}
