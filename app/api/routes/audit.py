from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import datetime

from app.db.session import get_db
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditEventResponse, AuditFilter
from app.models.user import User, UserRole
from app.core.permissions import get_current_user, require_roles

router = APIRouter(prefix="/audit", tags=["Audit"])
DBSession = Annotated[AsyncSession, Depends(get_db)]

STEWARD_OU_ADMIN = (UserRole.DATA_STEWARD, UserRole.ADMIN)


@router.get("/events", response_model=list[AuditEventResponse])
async def list_audit_events(
    db: DBSession,
    actor_id: Optional[int] = Query(None, description="Filtrer par ID de l'acteur"),
    resource_type: Optional[str] = Query(None, description="Filtrer par type de ressource (dataset, access_request)"),
    start_date: Optional[datetime.datetime] = Query(None, description="Date de début (inclusive)"),
    end_date: Optional[datetime.datetime] = Query(None, description="Date de fin (inclusive)"),
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    current_user: User = Depends(
        require_roles(
            *STEWARD_OU_ADMIN,
            message="Seul un data steward ou admin peut consulter l'audit",
        )
    ),
):
    filters = AuditFilter(
        actor_id=actor_id,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date
    )
    repo = AuditRepository(db)
    return await repo.get_events(filters, skip, limit)