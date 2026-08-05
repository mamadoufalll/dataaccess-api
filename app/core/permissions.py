from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Predicats purs (testables unitairement) 

def is_data_steward(user: User) -> bool:
    return user.role == UserRole.DATA_STEWARD


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


def can_publish(user: User) -> bool:
    return user.role in (UserRole.DATA_STEWARD, UserRole.ADMIN)


def can_reject(user: User) -> bool:
    return user.role in (UserRole.DATA_STEWARD, UserRole.ADMIN)


def is_owner(user: User, owner_id: int) -> bool:
    return user.id == owner_id
def can_decide_on_dataset(user: User, dataset) -> bool:
    """Un admin decide partout ; un data steward uniquement dans son domaine.

    Un dataset sans domaine reste instruisible par tout steward, faute de
    cloisonnement applicable.
    """
    if is_admin(user):
        return True
    if not is_data_steward(user):
        return False
    if dataset.domain is None:
        return True
    return user.domain == dataset.domain


# Dependances FastAPI (centralisation du RBAC) 

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Verifie le token et retourne l'utilisateur courant."""
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    repo = UserRepository(db)
    user = await repo.get(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce compte est desactive.",
        )
    return user


def require_roles(*roles: UserRole, message: str = "Habilitation insuffisante"):
    """Fabrique une dependance FastAPI exigeant l'un des roles donnes."""

    def _dependance(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=message
            )
        return current_user

    return _dependance
