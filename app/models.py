from sqlalchemy import String, Float, Text, Enum, ForeignKey, func, DateTime, Uuid
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Volcano(Base):
    __tablename__ = "volcanoes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4())) 
    # Note: gen_random_uuid() is Postgres specific function, for SQLAlchemy insert usually better to handle UUID in Python or let DB handle it. 
    # But since user wants exact SQL match, we'll map fields. 
    # However, SQLAlchemy `default` expects a python callable usually. 
    # To keep it simple and compatible with existing patterns, we might rely on Python's uuid or server_default.
    
    # Let's stick closer to the user's SQL types.
    
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    province: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    current_status: Mapped["VolcanoStatusCurrent"] = relationship(back_populates="volcano", uselist=False, cascade="all, delete-orphan")
    history: Mapped[list["VolcanoStatusHistory"]] = relationship(back_populates="volcano", cascade="all, delete-orphan")

class VolcanoStatusCurrent(Base):
    __tablename__ = "volcano_status_current"

    volcano_id: Mapped[str] = mapped_column(ForeignKey("volcanoes.id", ondelete="CASCADE"), primary_key=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False) # In older SQLA or generic, Enum can be tricky, String is safe.
    status_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(Text, server_default="PVMBG/MAGMA")
    observed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    volcano: Mapped["Volcano"] = relationship(back_populates="current_status")

class VolcanoStatusHistory(Base):
    __tablename__ = "volcano_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    volcano_id: Mapped[str] = mapped_column(ForeignKey("volcanoes.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    status_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(Text, server_default="PVMBG/MAGMA")
    observed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    volcano: Mapped["Volcano"] = relationship(back_populates="history")
