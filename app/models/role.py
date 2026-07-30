from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum

class RoleType(str, enum.Enum):
    PRODUCER = "producer"
    REQUESTER = "requester"
    DATA_STEWARD = "data_steward"
    ADMIN = "admin"

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

