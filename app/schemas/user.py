# app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.user import UserRole  
import datetime


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="Nom d'utilisateur")
    email: EmailStr = Field(description="Adresse email valide")
    password: str = Field(min_length=8, max_length=100, description="Mot de passe (8 caractères minimum)")

 
class UserLogin(BaseModel):
    username: str = Field(description="Nom d'utilisateur")
    password: str = Field(description="Mot de passe")


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole  
    is_active: bool
    created_at: datetime.datetime

    # Cette configuration permet de convertir un objet SQLAlchemy en Pydantic
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None