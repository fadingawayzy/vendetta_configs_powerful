from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from config import config

print(f"🔌 Connecting to Database at: {config.database.host}:{config.database.port}")

DATABASE_URL = config.database.url

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=2,
    max_overflow=0,
    pool_recycle=600,
    pool_pre_ping=True,        # Проверяет соединение перед использованием
    pool_timeout=10,
    poolclass=AsyncAdaptedQueuePool,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
async_session_maker = async_session


async def init_models():
    print("🔄 Initializing database models...")
    from database.models.base import Base
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise