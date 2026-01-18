from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    slot_id: Mapped[int] = mapped_column(Integer, default=1)
    custom_countries: Mapped[str] = mapped_column(String(50), nullable=True)
    config_limit: Mapped[int] = mapped_column(Integer, default=10)
