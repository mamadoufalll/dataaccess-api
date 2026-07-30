import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture(scope="function")
async def auth_client():
    """
    Fixture qui crée un utilisateur, se connecte, et retourne un client authentifié.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Inscription
        await client.post(
            "/auth/register",
            json={"username": "testdataset", "email": "dataset@example.com", "password": "datasetpass"}
        )
        # Connexion pour obtenir le token
        login_resp = await client.post(
            "/auth/login",
            data={"username": "testdataset", "password": "datasetpass"}
        )
        token = login_resp.json()["access_token"]
        # Ajouter le token au client pour les requêtes suivantes
        client.headers = {"Authorization": f"Bearer {token}"}
        yield client

@pytest.mark.asyncio
async def test_create_dataset(auth_client):
    response = await auth_client.post(
        "/datasets/",
        json={
            "name": "Test Dataset",
            "description": "Un dataset pour les tests",
            "classification": "internal",
            "purpose": "Testing",
            "retention_days": 365,
            "contact": "test@example.com"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "draft"
    assert data["name"] == "Test Dataset"

@pytest.mark.asyncio
async def test_submit_dataset(auth_client):
    create_resp = await auth_client.post(
        "/datasets/",
        json={
            "name": "Dataset to submit",
            "description": "Soumission test",
            "classification": "confidential",
            "purpose": "Test submit",
            "retention_days": 180,
            "contact": "submit@example.com"
        }
    )
    dataset_id = create_resp.json()["id"]

    submit_resp = await auth_client.patch(f"/datasets/{dataset_id}/submit")
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "submitted"

@pytest.mark.asyncio
async def test_publish_dataset(auth_client):
    create_resp = await auth_client.post(
        "/datasets/",
        json={
            "name": "Dataset to publish",
            "description": "Publication test",
            "classification": "public",
            "purpose": "Test publish",
            "retention_days": 30,
            "contact": "publish@example.com"
        }
    )
    dataset_id = create_resp.json()["id"]

    # Soumettre
    await auth_client.patch(f"/datasets/{dataset_id}/submit")

    # Publier (l'utilisateur a le rôle REQUESTER par défaut, donc 403)
    publish_resp = await auth_client.patch(f"/datasets/{dataset_id}/publish")
    assert publish_resp.status_code == 403
