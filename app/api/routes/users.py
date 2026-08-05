from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdate
from app.models.user import User, UserRole
from app.core.permissions import get_current_user, require_roles, is_admin

router = APIRouter(prefix="/users", tags=["Users"])
DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Retourne les informations de l'utilisateur connecté."""
    return current_user


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: DBSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            message="Seul un administrateur peut lister les utilisateurs",
        )
    ),
):
    """Liste tous les utilisateurs (réservé aux administrateurs)."""
    repo = UserRepository(db)
    return await repo.get_all(skip, limit)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: DBSession,
    current_user: User = Depends(get_current_user)
):
    """Met à jour un utilisateur (admin, ou l'utilisateur lui-même pour ses propres champs)."""
    est_admin = is_admin(current_user)

    if current_user.id != user_id and not est_admin:
        raise HTTPException(403, "Vous n'êtes pas autorisé à modifier cet utilisateur")

    # Seul un administrateur peut changer un rôle ou activer/désactiver un compte
    if not est_admin:
        if data.role is not None:
            raise HTTPException(403, "Seul un administrateur peut modifier un rôle")
        if data.is_active is not None:
            raise HTTPException(403, "Seul un administrateur peut activer ou désactiver un compte")

    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")
    updated = await repo.update(user_id, data)
    return updated