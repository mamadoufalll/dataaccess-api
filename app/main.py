from fastapi import FastAPI

from app.core.config import settings
from app.api.routes import auth, datasets, users, access_requests, audit
from app.middlewares.request_id import RequestIDMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware

# Création de l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="API de gouvernance de données - DataAccess",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Routeurs
app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(users.router)
app.include_router(access_requests.router)
app.include_router(audit.router)


# Endpoint de base
@app.get("/", tags=["Health"])
async def root():
    return {"message": f"Bienvenue sur {settings.APP_NAME}"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Vérification de santé du service, utilisée par Docker."""
    return {"status": "healthy"}