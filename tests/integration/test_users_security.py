import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest_asyncio.fixture(scope="function")
async def client_requester():
    """Utilisateur ordinaire (role requester par defaut)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/auth/register",
            json={"username": "simple", "email": "simple@example.com", "password": "motdepasse1"},
        )
        login = await client.post(
            "/auth/login",
            data={"username": "simple", "password": "motdepasse1"},
        )
        client.headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        yield client


@pytest.mark.asyncio
async def test_un_utilisateur_ne_peut_pas_se_promouvoir_admin(client_requester):
    """Escalade de privileges : un requester tente de devenir admin."""
    moi = await client_requester.get("/users/me")
    mon_id = moi.json()["id"]

    reponse = await client_requester.patch(f"/users/{mon_id}", json={"role": "admin"})

    assert reponse.status_code == 403
    apres = await client_requester.get("/users/me")
    assert apres.json()["role"] == "requester"


@pytest.mark.asyncio
async def test_un_utilisateur_ne_peut_pas_se_promouvoir_data_steward(client_requester):
    moi = await client_requester.get("/users/me")
    mon_id = moi.json()["id"]

    reponse = await client_requester.patch(f"/users/{mon_id}", json={"role": "data_steward"})

    assert reponse.status_code == 403


@pytest.mark.asyncio
async def test_un_utilisateur_peut_modifier_son_email(client_requester):
    """Les champs non sensibles restent modifiables par l'interesse."""
    moi = await client_requester.get("/users/me")
    mon_id = moi.json()["id"]

    reponse = await client_requester.patch(
        f"/users/{mon_id}", json={"email": "nouveau@example.com"}
    )

    assert reponse.status_code == 200
    assert reponse.json()["email"] == "nouveau@example.com"


@pytest.mark.asyncio
async def test_lister_les_utilisateurs_est_reserve_a_l_admin(client_requester):
    reponse = await client_requester.get("/users/")
    assert reponse.status_code == 403