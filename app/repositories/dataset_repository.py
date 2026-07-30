from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.dataset import Dataset, DatasetStatus
from app.schemas.dataset import DatasetCreate, DatasetUpdate

class DatasetRepository(BaseRepository[Dataset, DatasetCreate, DatasetUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(Dataset, db)

    async def get_by_owner(self, owner_id: int, skip: int = 0, limit: int = 20) -> list[Dataset]:
        result = await self.db.execute(
            select(Dataset)
            .where(Dataset.owner_id == owner_id)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_public(self, skip: int = 0, limit: int = 20) -> list[Dataset]:
        result = await self.db.execute(
            select(Dataset)
            .where(Dataset.status == DatasetStatus.PUBLISHED)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(self, dataset_id: int, new_status: DatasetStatus) -> Dataset | None:
        dataset = await self.get(dataset_id)
        if not dataset:
            return None
        dataset.status = new_status
        await self.db.flush()
        await self.db.refresh(dataset)
        return dataset
