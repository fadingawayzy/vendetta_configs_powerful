from sqlalchemy import Text, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class RawConfig(Base):
    __tablename__ = "raw_candidates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_link: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50))
    # Можно добавить created_at, чтобы чистить старое