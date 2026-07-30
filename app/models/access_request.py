# app/models/access_request.py
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import datetime
import enum

class AccessStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class AccessRequest(Base):
    __tablename__ = "access_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    requested_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AccessStatus] = mapped_column(SQLAlchemyEnum(AccessStatus), default=AccessStatus.PENDING, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(onupdate=datetime.datetime.utcnow)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True) 
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relations (optionnelles)
    dataset = relationship("Dataset", back_populates="access_requests")
    requester = relationship("User", foreign_keys=[requester_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])