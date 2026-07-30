from pydantic import BaseModel, Field
from typing import Optional
from app.models.access_request import AccessStatus
import datetime

class AccessRequestCreate(BaseModel):
    justification: str = Field(..., min_length=10, max_length=500)
    requested_duration_days: int = Field(..., ge=1, le=365)

class AccessRequestUpdate(BaseModel):
    status: AccessStatus
    review_comment: Optional[str] = Field(None, max_length=200)

class AccessRequestResponse(BaseModel):
    id: int
    dataset_id: int
    requester_id: int
    justification: str
    requested_duration_days: int
    status: AccessStatus
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime]
    reviewed_by: Optional[int]
    review_comment: Optional[str]

    model_config = {"from_attributes": True}
