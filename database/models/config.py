from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from database.models.base import Base


class Config(Base):
    __tablename__ = "configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    uuid = Column(String, unique=True, index=True, nullable=False)
    link = Column(Text, nullable=False)

    name = Column(String, default="NoName")
    source = Column(String, default="unknown")

    host = Column(String)
    port = Column(Integer)
    protocol = Column(String, default="vless")
    security = Column(String, default="none")
    sni = Column(String, nullable=True)

    ping = Column(Integer)
    country = Column(String(2))
    flag = Column(String)
    tier = Column(Integer, default=3)

    is_active = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("uuid", name="uq_config_uuid"),)

    def __repr__(self):
        return f"<Config(uuid={self.uuid}, ip={self.host}, ping={self.ping})>"
