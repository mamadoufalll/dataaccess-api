# app/models/audit_event.py
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import datetime

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow, nullable=False)

    actor = relationship("User", foreign_keys=[actor_id])