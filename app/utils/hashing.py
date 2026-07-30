from app.core.security import hash_password, verify_password

# Ce fichier est un wrapper pour respecter l'architecture.
# Toute la logique de hachage est déjà dans core/security.py.
__all__ = ["hash_password", "verify_password"]
