from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, Integer, Text, String, Index, DateTime, func
from datetime import datetime


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    slot_id: Mapped[int] = mapped_column(Integer, default=1)
    custom_countries: Mapped[str] = mapped_column(String(50), nullable=True)
    config_limit: Mapped[int] = mapped_column(Integer, default=10)


class Config(Base):
    __tablename__ = "configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_link: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str] = mapped_column(String(10), index=True)
    flag: Mapped[str] = mapped_column(String(10))
    ping: Mapped[int] = mapped_column(Integer, index=True)  # <--- ДОБАВЛЕН INDEX
    source: Mapped[str] = mapped_column(String(50))
    tier: Mapped[int] = mapped_column(Integer, default=3, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Составной индекс для супер-быстрых выборок
    __table_args__ = (
        Index('ix_country_ping', 'country', 'ping'),
    )