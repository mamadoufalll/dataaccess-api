import os
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Forcer l'utilisation de SQLite en mémoire pour les tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# Créer un moteur SQLite asynchrone
test_engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
TestingSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)

# Remplacer la dépendance get_db par la version de test
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True, scope="function")
async def create_tables():
    """Crée les tables avant chaque test et les supprime après."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
