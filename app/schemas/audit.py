from pydantic import BaseModel
from typing import Optional
import datetime

class AuditEventResponse(BaseModel):
    id: int
    actor_id: int
    action: str
    resource_type: str
    resource_id: int
    details: Optional[str]
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

class AuditFilter(BaseModel):
    actor_id: Optional[int] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None
