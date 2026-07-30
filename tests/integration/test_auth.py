import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_success():
    """
    Teste l'inscription d'un nouvel utilisateur.
    Doit retourner 201 avec les informations de l'utilisateur (sans mot de passe).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password" not in data  # Vérifie que le mot de passe n'est pas retourné

@pytest.mark.asyncio
async def test_register_duplicate_username():
    """
    Vérifie qu'on ne peut pas créer deux comptes avec le même nom d'utilisateur.
    Doit retourner 409 Conflict.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Inscrire un premier utilisateur
        await client.post(
            "/auth/register",
            json={"username": "dupuser", "email": "dup@example.com", "password": "password123"}
        )
        # Essayer d'inscrire un second avec le même username
        response = await client.post(
            "/auth/register",
            json={"username": "dupuser", "email": "dup2@example.com", "password": "password456"}
        )
    assert response.status_code == 409
    assert "déjà pris" in response.text

@pytest.mark.asyncio
async def test_login_success():
    """
    Teste la connexion avec des identifiants valides.
    Doit retourner 200 avec un access_token.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Créer un utilisateur
        await client.post(
            "/auth/register",
            json={"username": "loginuser", "email": "login@example.com", "password": "loginpass123"}
        )
        # Se connecter
        response = await client.post(
            "/auth/login",
            data={
                "username": "loginuser",
                "password": "loginpass123"
            }
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_login_wrong_password():
    """
    Teste la connexion avec un mauvais mot de passe.
    Doit retourner 401 Unauthorized.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/auth/register",
            json={"username": "wrongpass", "email": "wrong@example.com", "password": "correctpass"}
        )
        response = await client.post(
            "/auth/login",
            data={
                "username": "wrongpass",
                "password": "wrongpass"
            }
        )
    assert response.status_code == 401