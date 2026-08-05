from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.access_request_repository import AccessRequestRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.access_request import AccessRequestCreate, AccessRequestResponse, AccessRequestUpdate
from app.models.user import User, UserRole
from app.models.dataset import DatasetStatus
from app.models.access_request import AccessStatus
from app.core.permissions import get_current_user, require_roles, can_decide_on_dataset

router = APIRouter(prefix="/access-requests", tags=["Access Requests"])
DBSession = Annotated[AsyncSession, Depends(get_db)]

STEWARD_OU_ADMIN = (UserRole.DATA_STEWARD, UserRole.ADMIN)


@router.post("/", response_model=AccessRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_access_request(
    dataset_id: int,
    data: AccessRequestCreate,
    db: DBSession,
    current_user: User = Depends(get_current_user)
):
    # Vérifier que le dataset existe et est publié
    dataset_repo = DatasetRepository(db)
    dataset = await dataset_repo.get(dataset_id)
    if not dataset or dataset.status != DatasetStatus.PUBLISHED:
        raise HTTPException(404, "Dataset non trouvé ou non publié")

    # Vérifier que l'utilisateur n'a pas déjà une demande en attente sur ce dataset
    repo = AccessRequestRepository(db)
    pending = await repo.get_pending_by_dataset(dataset_id)
    if any(req.requester_id == current_user.id for req in pending):
        raise HTTPException(409, "Vous avez déjà une demande en attente pour ce dataset")

    return await repo.create_for_requester(data, dataset_id, current_user.id)


@router.get("/pending", response_model=list[AccessRequestResponse])
async def get_pending_requests(
    db: DBSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: User = Depends(
        require_roles(
            *STEWARD_OU_ADMIN,
            message="Seul un data steward ou admin peut voir les demandes en attente",
        )
    ),
):
    repo = AccessRequestRepository(db)
    return await repo.get_pending_all(skip, limit)


@router.get("/me", response_model=list[AccessRequestResponse])
async def get_my_requests(
    db: DBSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: User = Depends(get_current_user)
):
    repo = AccessRequestRepository(db)
    return await repo.get_by_requester(current_user.id, skip, limit)


@router.patch("/{request_id}/decision", response_model=AccessRequestResponse)
async def decide_access_request(
    request_id: int,
    data: AccessRequestUpdate,
    db: DBSession,
    current_user: User = Depends(
        require_roles(
            *STEWARD_OU_ADMIN,
            message="Seul un data steward ou admin peut prendre une décision",
        )
    ),
):
    repo = AccessRequestRepository(db)
    access_req = await repo.get(request_id)
    if not access_req:
        raise HTTPException(404, "Demande d'accès non trouvée")
    if access_req.status != AccessStatus.PENDING:
        raise HTTPException(400, "Cette demande a déjà été traitée")

    # Cloisonnement par domaine : un steward n'instruit que son périmètre
    dataset_repo = DatasetRepository(db)
    dataset = await dataset_repo.get(access_req.dataset_id)
    if not can_decide_on_dataset(current_user, dataset):
        raise HTTPException(403, "Ce dataset ne relève pas de votre domaine")

    # Mettre à jour la demande
    update_data = data.model_dump()
    update_data["reviewed_by"] = current_user.id
    updated = await repo.update(request_id, AccessRequestUpdate(**update_data))

    # Enregistrer l'événement d'audit
    audit_repo = AuditRepository(db)
    await audit_repo.create_event(
        actor_id=current_user.id,
        action=f"ACCESS_{data.status.value.upper()}",
        resource_type="access_request",
        resource_id=request_id,
        details=f"Demande d'accès {data.status.value} pour le dataset {access_req.dataset_id}"
    )

    return updated