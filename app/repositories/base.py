# app/repositories/base.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import TypeVar, Generic, Type, Optional, Sequence
from pydantic import BaseModel

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchema, UpdateSchema]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    # LIRE
    async def get(self, id: int) -> Optional[ModelType]:
        """Récupère un enregistrement par son ID."""
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Récupère une liste paginée."""
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    # CRÉER
    async def create(self, data: CreateSchema) -> ModelType:
        """Crée un nouvel enregistrement."""
        instance = self.model(**data.model_dump())
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    # METTRE À JOUR
    async def update(self, id: int, data: UpdateSchema) -> Optional[ModelType]:
        """Met à jour un enregistrement (champs non nuls uniquement)."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get(id)
        await self.db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
        )
        await self.db.commit()
        return await self.get(id)

    # SUPPRIMER
    async def delete(self, id: int) -> bool:
        """Supprime un enregistrement. Retourne True si supprimé."""
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0