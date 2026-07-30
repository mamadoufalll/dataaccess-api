from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.audit_event import AuditEvent
from app.schemas.audit import AuditEventResponse, AuditFilter

class AuditRepository(BaseRepository[AuditEvent, None, None]):
    def __init__(self, db: AsyncSession):
        super().__init__(AuditEvent, db)

    async def create_event(
        self,
        actor_id: int,
        action: str,
        resource_type: str,
        resource_id: int,
        details: str | None = None
    ) -> AuditEvent:
        event = AuditEvent(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def get_events(
        self,
        filters: AuditFilter | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> list[AuditEvent]:
        query = select(AuditEvent)
        if filters:
            if filters.actor_id:
                query = query.where(AuditEvent.actor_id == filters.actor_id)
            if filters.resource_type:
                query = query.where(AuditEvent.resource_type == filters.resource_type)
            if filters.start_date:
                query = query.where(AuditEvent.created_at >= filters.start_date)
            if filters.end_date:
                query = query.where(AuditEvent.created_at <= filters.end_date)
        query = query.offset(skip).limit(limit).order_by(AuditEvent.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
