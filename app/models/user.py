from app.utils.time import utcnow_naive
# app/models/user.py

from sqlalchemy import String, Boolean, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import datetime
import enum


class UserRole(str, enum.Enum):
    PRODUCER = "producer"
    REQUESTER = "requester"
    DATA_STEWARD = "data_steward"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLAlchemyEnum(UserRole), default=UserRole.REQUESTER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(default=utcnow_naive)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        default=utcnow_naive,
        onupdate=utcnow_naive,
        nullable=True
    )

  
    datasets: Mapped[list["Dataset"]] = relationship(back_populates="owner")