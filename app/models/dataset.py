from app.utils.time import utcnow_naive
from sqlalchemy import String, Integer, Text, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import datetime
import enum

class DatasetStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PUBLISHED = "published"
    REJECTED = "rejected"

class Classification(str, enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification: Mapped[Classification] = mapped_column(
        SQLAlchemyEnum(Classification),
        default=Classification.PUBLIC,
        nullable=False
    )
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[DatasetStatus] = mapped_column(
        SQLAlchemyEnum(DatasetStatus),
        default=DatasetStatus.DRAFT,
        nullable=False
    )

    created_at: Mapped[datetime.datetime] = mapped_column(default=utcnow_naive)
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        default=utcnow_naive,
        onupdate=utcnow_naive,
        nullable=True
    )

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship(back_populates="datasets")
    access_requests: Mapped[list["AccessRequest"]] = relationship(back_populates="dataset")