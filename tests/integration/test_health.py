import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_repond_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reponse = await client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_health_ne_demande_pas_d_authentification():
    """Docker doit pouvoir interroger /health sans token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reponse = await client.get("/health")
    assert reponse.status_code != 401


@pytest.mark.asyncio
async def test_racine_repond_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reponse = await client.get("/")
    assert reponse.status_code == 200
