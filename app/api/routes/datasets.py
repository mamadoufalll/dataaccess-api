from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.dataset import DatasetCreate, DatasetResponse, DatasetUpdate
from app.models.user import User, UserRole
from app.models.dataset import Dataset, DatasetStatus
from app.api.routes.auth import get_current_user
from app.core.permissions import can_publish, can_reject, is_owner

router = APIRouter(prefix="/datasets", tags=["Datasets"])
DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("/", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    data: DatasetCreate,
    db: DBSession,
    current_user: User = Depends(get_current_user)
):
    dataset = Dataset(
        name=data.name,
        description=data.description,
        classification=data.classification,
        purpose=data.purpose,
        retention_days=data.retention_days,
        contact=data.contact,
        owner_id=current_user.id
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.get("/", response_model=list[DatasetResponse])
async def list_datasets(
    db: DBSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    public_only: bool = False,
    owner_id: Optional[int] = None,
):
    repo = DatasetRepository(db)
    if public_only:
        return await repo.get_public(skip, limit)
    if owner_id:
        return await repo.get_by_owner(owner_id, skip, limit)
    return await repo.get_all(skip, limit)


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    db: DBSession,
    current_user: User = Depends(get_current_user)
):
    repo = DatasetRepository(db)
    dataset = await repo.get(dataset_id)
    if not dataset:
        raise HTTPException(404, "Dataset non trouvé")
    if dataset.status != DatasetStatus.PUBLISHED and dataset.owner_id != current_user.id:
        raise HTTPException(403, "Vous n'êtes pas autorisé à voir ce dataset")
    return dataset


@router.patch("/{dataset_id}/submit", response_model=DatasetResponse)
async def submit_dataset(
    dataset_id: int,
    db: DBSession,
    current_user: User = Depends(get_current_user)
):
    repo = DatasetRepository(db)
    dataset = await repo.get(dataset_id)
    if not dataset:
        raise HTTPException(404, "Dataset non trouvé")
    if dataset.owner_id != current_user.id:
        raise HTTPException(403, "Vous n'êtes pas le propriétaire")
    if dataset.status != DatasetStatus.DRAFT:
        raise HTTPException(400, "Seul un brouillon peut être soumis")
    if not dataset.classification or not dataset.purpose or not dataset.retention_days or not dataset.contact:
        raise HTTPException(400, "Le dataset doit avoir classification, purpose, retention_days et contact pour être soumis")
    updated = await repo.update_status(dataset_id, DatasetStatus.SUBMITTED)
    return updated


@router.patch("/{dataset_id}/publish", response_model=DatasetResponse)
async def publish_dataset(
    dataset_id: int,
    db: DBSession,
    current_user: User = Depends(get_current_user)
):
    
    print(f"🔍 [PUBLISH] Utilisateur ID={current_user.id}, rôle={repr(current_user.role)}, type={type(current_user.role)}")

    
    if current_user.role not in (UserRole.DATA_STEWARD, UserRole.ADMIN):
        print(f" Accès refusé pour rôle {current_user.role}")
        raise HTTPException(403, "Seul un data steward ou admin peut publier")

    repo = DatasetRepository(db)
    dataset = await repo.get(dataset_id)
    if not dataset:
        raise HTTPException(404, "Dataset non trouvé")
    if dataset.status != DatasetStatus.SUBMITTED:
        raise HTTPException(400, "Seul un dataset soumis peut être publié")
    updated = await repo.update_status(dataset_id, DatasetStatus.PUBLISHED)
    return updated


@router.patch("/{dataset_id}/reject", response_model=DatasetResponse)
async def reject_dataset(
    dataset_id: int,
    db: DBSession,
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in (UserRole.DATA_STEWARD, UserRole.ADMIN):
        raise HTTPException(403, "Seul un data steward ou admin peut rejeter")
    repo = DatasetRepository(db)
    dataset = await repo.get(dataset_id)
    if not dataset:
        raise HTTPException(404, "Dataset non trouvé")
    if dataset.status != DatasetStatus.SUBMITTED:
        raise HTTPException(400, "Seul un dataset soumis peut être rejeté")
    updated = await repo.update_status(dataset_id, DatasetStatus.REJECTED)
    return updated