
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#  ALGORITHME JWT
ALGORITHM = "HS256" 


#  FONCTIONS DE HACHAGE DES MOTS DE PASSE


def hash_password(password: str) -> str:
    """
    Transforme un mot de passe en clair en un hash irréversible.
    Utilise un "salt" aléatoire généré automatiquement par bcrypt.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si un mot de passe en clair correspond bien au hash stocké.
    Retourne True si c'est le cas.
    """
    return pwd_context.verify(plain_password, hashed_password)


#  FONCTIONS DE GESTION DES TOKENS JWT


def create_access_token(
    subject: str | int,
    extra_data: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None
) -> str:
    """
    Génère un token JWT d'accès.
    - subject : l'identifiant de l'utilisateur (ex: son ID).
    - extra_data : données supplémentaires à ajouter (ex: son rôle).
    - expires_delta : durée de validité (sinon, on prend la valeur de config).
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(subject),  # "sub" = subject (standard JWT)
        "exp": expire,        # Date d'expiration
        "iat": datetime.now(timezone.utc),  # "iat" = issued at (création)
        "type": "access",
    }
    if extra_data:
        payload.update(extra_data)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(subject: str | int) -> str:
    """
    Génère un token de rafraîchissement (plus longue durée).
    Permet de renouveler l'access token sans se reconnecter.
    """
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict[str, Any]:
    """
    Décode un token JWT, vérifie sa signature et son expiration.
    Si le token est invalide (signature erronée, expiré, malformé),
    on lève une exception HTTP 401 (Non autorisé).
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError as e:
        # On lève une erreur HTTP 401 avec un message approprié
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalide: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )