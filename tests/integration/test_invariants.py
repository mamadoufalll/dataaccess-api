import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.user import User, UserRole
from tests.conftest import TestingSessionLocal


async def promouvoir(username: str, role: UserRole) -> None:
    """Change le role d'un utilisateur directement en base (setup de test)."""
    async with TestingSessionLocal() as session:
        resultat = await session.execute(
            select(User).where(User.username == username)
        )
        utilisateur = resultat.scalar_one()
        utilisateur.role = role
        await session.commit()


async def inscrire_et_connecter(client: AsyncClient, username: str) -> str:
    await client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "motdepasse1",
        },
    )
    login = await client.post(
        "/auth/login", data={"username": username, "password": "motdepasse1"}
    )
    return login.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def client_producteur():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        token = await inscrire_et_connecter(client, "producteur")
        await promouvoir("producteur", UserRole.PRODUCER)
        client.headers = {"Authorization": f"Bearer {token}"}
        yield client


@pytest_asyncio.fixture(scope="function")
async def client_steward():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        token = await inscrire_et_connecter(client, "steward")
        await promouvoir("steward", UserRole.DATA_STEWARD)
        client.headers = {"Authorization": f"Bearer {token}"}
        yield client


@pytest.mark.asyncio
async def test_un_producteur_ne_peut_pas_publier_son_dataset(client_producteur):
    """Exigence du sujet : la publication passe obligatoirement par une validation."""
    creation = await client_producteur.post(
        "/datasets/",
        json={
            "name": "Dataset du producteur",
            "description": "Tentative de publication directe",
            "classification": "internal",
            "purpose": "Test invariant",
            "retention_days": 90,
            "contact": "producteur@example.com",
        },
    )
    assert creation.status_code == 201
    dataset_id = creation.json()["id"]

    await client_producteur.patch(f"/datasets/{dataset_id}/submit")

    publication = await client_producteur.patch(f"/datasets/{dataset_id}/publish")
    assert publication.status_code == 403

    verification = await client_producteur.get(f"/datasets/{dataset_id}")
    assert verification.json()["status"] == "submitted"


@pytest.mark.asyncio
async def test_un_producteur_ne_peut_pas_voir_les_demandes_en_attente(client_producteur):
    """Isolation : l'instruction des demandes est reservee aux stewards."""
    reponse = await client_producteur.get("/access-requests/pending")
    assert reponse.status_code == 403


@pytest.mark.asyncio
async def test_un_producteur_ne_peut_pas_consulter_l_audit(client_producteur):
    reponse = await client_producteur.get("/audit/events")
    assert reponse.status_code == 403


@pytest.mark.asyncio
async def test_un_steward_peut_publier_un_dataset_soumis(client_steward):
    """Cas nominal symetrique : le steward, lui, publie."""
    creation = await client_steward.post(
        "/datasets/",
        json={
            "name": "Dataset a valider",
            "description": "Publication legitime",
            "classification": "public",
            "purpose": "Test nominal",
            "retention_days": 30,
            "contact": "steward@example.com",
        },
    )
    dataset_id = creation.json()["id"]

    await client_steward.patch(f"/datasets/{dataset_id}/submit")
    publication = await client_steward.patch(f"/datasets/{dataset_id}/publish")

    assert publication.status_code == 200
    assert publication.json()["status"] == "published"