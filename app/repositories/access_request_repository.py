from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.access_request import AccessRequest, AccessStatus
from app.schemas.access_request import AccessRequestCreate, AccessRequestUpdate

class AccessRequestRepository(BaseRepository[AccessRequest, AccessRequestCreate, AccessRequestUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(AccessRequest, db)

    async def get_pending_by_dataset(self, dataset_id: int) -> list[AccessRequest]:
        result = await self.db.execute(
            select(AccessRequest)
            .where(
                AccessRequest.dataset_id == dataset_id,
                AccessRequest.status == AccessStatus.PENDING
            )
        )
        return list(result.scalars().all())

    async def get_pending_all(self, skip: int = 0, limit: int = 20) -> list[AccessRequest]:
        result = await self.db.execute(
            select(AccessRequest)
            .where(AccessRequest.status == AccessStatus.PENDING)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_requester(self, requester_id: int, skip: int = 0, limit: int = 20) -> list[AccessRequest]:
        result = await self.db.execute(
            select(AccessRequest)
            .where(AccessRequest.requester_id == requester_id)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create_for_requester(
        self, data: AccessRequestCreate, dataset_id: int, requester_id: int
    ) -> AccessRequest:
        """Crée une demande d'accès en statut PENDING."""
        demande = AccessRequest(
            **data.model_dump(),
            dataset_id=dataset_id,
            requester_id=requester_id,
            status=AccessStatus.PENDING,
        )
        self.db.add(demande)
        await self.db.commit()
        await self.db.refresh(demande)
        return demande