from pydantic import BaseModel, Field


class Token(BaseModel):
    """Reponse renvoyee apres une authentification reussie."""

    access_token: str = Field(description="JWT d'acces")
    refresh_token: str = Field(description="JWT de rafraichissement")
    token_type: str = Field(default="bearer", description="Type de jeton")
    expires_in: int = Field(description="Duree de validite du token d'acces, en secondes")


class TokenRefresh(BaseModel):
    """Corps attendu pour renouveler un jeton d'acces."""

    refresh_token: str = Field(description="JWT de rafraichissement")


class TokenPayload(BaseModel):
    """Contenu decode d'un JWT."""

    sub: str | None = None
    exp: int | None = None
    type: str | None = None