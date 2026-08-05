import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.user import User, UserRole
from tests.conftest import TestingSessionLocal


async def configurer(username: str, role: UserRole, domaine: str | None = None) -> None:
    """Affecte un role et un domaine directement en base (setup de test)."""
    async with TestingSessionLocal() as session:
        resultat = await session.execute(select(User).where(User.username == username))
        utilisateur = resultat.scalar_one()
        utilisateur.role = role
        utilisateur.domain = domaine
        await session.commit()


async def creer_client(username: str) -> AsyncClient:
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
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
    client.headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    return client


@pytest_asyncio.fixture(scope="function")
async def contexte():
    """Un dataset publie du domaine 'finance' et une demande d'acces en attente."""
    steward_finance = await creer_client("steward_finance")
    await configurer("steward_finance", UserRole.DATA_STEWARD, "finance")

    steward_rh = await creer_client("steward_rh")
    await configurer("steward_rh", UserRole.DATA_STEWARD, "rh")

    demandeur = await creer_client("demandeur")

    creation = await steward_finance.post(
        "/datasets/",
        json={
            "name": "Budget 2026",
            "description": "Donnees budgetaires",
            "classification": "confidential",
            "purpose": "Pilotage",
            "retention_days": 365,
            "contact": "finance@example.com",
            "domain": "finance",
        },
    )
    dataset_id = creation.json()["id"]
    await steward_finance.patch(f"/datasets/{dataset_id}/submit")
    await steward_finance.patch(f"/datasets/{dataset_id}/publish")

    demande = await demandeur.post(
        f"/access-requests/?dataset_id={dataset_id}",
        json={"justification": "Analyse budgetaire", "requested_duration_days": 30},
    )

    yield {
        "steward_finance": steward_finance,
        "steward_rh": steward_rh,
        "demande_id": demande.json()["id"],
    }

    for c in (steward_finance, steward_rh, demandeur):
        await c.aclose()


@pytest.mark.asyncio
async def test_un_steward_d_un_autre_domaine_ne_peut_pas_decider(contexte):
    """Invariant : seul un steward du domaine du dataset instruit la demande."""
    reponse = await contexte["steward_rh"].patch(
        f"/access-requests/{contexte['demande_id']}/decision",
        json={"status": "approved"},
    )
    assert reponse.status_code == 403


@pytest.mark.asyncio
async def test_le_steward_du_domaine_peut_decider(contexte):
    """Cas nominal symetrique."""
    reponse = await contexte["steward_finance"].patch(
        f"/access-requests/{contexte['demande_id']}/decision",
        json={"status": "approved"},
    )
    assert reponse.status_code == 200