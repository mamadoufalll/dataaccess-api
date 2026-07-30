
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from app.core.config import settings

#  LE MOTEUR (le standard téléphonique)

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    pool_pre_ping=True,
    max_overflow=20
)

#  L'USINE À SESSIONS (le distributeur de caddies)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 3. LA DÉPENDANCE FASTAPI (le serveur qui donne un caddie à chaque client)

async def get_db() -> AsyncSession:
    """
    Générateur de session de base de données.
    À chaque requête HTTP, on crée une session, on la donne à la route,
    et on la ferme automatiquement après.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session            
            await session.commit()   
        except Exception:
            await session.rollback() 
            raise                    