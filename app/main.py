
from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import auth  
from app.api.routes import datasets
from app.middlewares.request_id import RequestIDMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware
from app.api.routes import users
from app.api.routes import access_requests, audit

# Création de l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="API de gouvernance de données - DataAccess",
    docs_url="/docs",
    redoc_url="/redoc",
)

# On branche le routeur d'authentification
app.include_router(auth.router)

# Endpoint de base 
@app.get("/")
async def root():
    return {"message": f"Bienvenue sur {settings.APP_NAME}"}

app.include_router(datasets.router)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(users.router)

app.include_router(access_requests.router)
app.include_router(audit.router)