from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.connection import async_session
from database.models.config import Config
from database.models.raw_config import RawConfig
from database.models.user import User


async def get_user_slot(user_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        return user.slot_id if user else 1


async def set_user_slot(user_id: int, slot: int):
    async with async_session() as session:
        # Используем __table__ для надежности
        stmt = pg_insert(User.__table__).values(user_id=user_id, slot_id=slot)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id"], set_=dict(slot_id=slot)
        )
        await session.execute(stmt)
        await session.commit()


async def set_user_filter(user_id: int, countries: list[str]):
    val = ",".join(countries) if countries else None

    async with async_session() as session:
        stmt = pg_insert(User.__table__).values(user_id=user_id, custom_countries=val)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id"], set_=dict(custom_countries=val)
        )
        await session.execute(stmt)
        await session.commit()


async def get_user_filter(user_id: int) -> list[str]:
    async with async_session() as session:
        res = await session.execute(
            select(User.custom_countries).where(User.user_id == user_id)
        )
        val = res.scalar_one_or_none()
        return val.split(",") if val else []

async def get_user_filter_count(user_id: int) -> int:
    async with async_session() as session:
        res = await session.execute(
            select(func.count(User.id)).where(User.user_id == user_id)
        )
        return res.scalar_one()


async def set_user_limit(user_id: int, limit: int):
    async with async_session() as session:
        stmt = pg_insert(User.__table__).values(user_id=user_id, config_limit=limit)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id"], set_=dict(config_limit=limit)
        )
        await session.execute(stmt)
        await session.commit()


async def get_user_settings(user_id: int):
    async with async_session() as session:
        res = await session.execute(select(User).where(User.user_id == user_id))
        user = res.scalar_one_or_none()

        limit = user.config_limit if user else 10
        countries = (
            user.custom_countries.split(",") if (user and user.custom_countries) else []
        )

        return countries, limit


async def clear_raw_table():
    async with async_session() as session:
        await session.execute(delete(RawConfig))
        await session.commit()


async def save_raw_batch(links: list[dict]):
    if not links:
        return
    async with async_session() as session:
        stmt = pg_insert(RawConfig.__table__).values(links)
        # on_conflict_do_nothing на случай дублей ссылок
        stmt = stmt.on_conflict_do_nothing()
        await session.execute(stmt)
        await session.commit()


async def get_raw_batch(limit: int, offset: int):
    async with async_session() as session:
        res = await session.execute(select(RawConfig).limit(limit).offset(offset))
        return res.scalars().all()


async def count_raw_configs():
    async with async_session() as session:
        return await session.scalar(select(func.count(RawConfig.id)))


async def clear_configs_table():
    async with async_session() as session:
        await session.execute(delete(Config))
        await session.commit()


async def save_configs_batch(configs_list: list):
    """Старая функция, исправлена для совместимости"""
    if not configs_list:
        return
    async with async_session() as session:
        stmt = pg_insert(Config.__table__).values(configs_list)
        stmt = stmt.on_conflict_do_nothing(index_elements=["uuid"])
        await session.execute(stmt)
        await session.commit()


async def get_configs_by_country(country_code: str, limit: int = 3):
    async with async_session() as session:
        result = await session.execute(
            select(Config)
            .where(Config.country == country_code)
            .order_by(Config.ping.asc())
            .limit(limit)
        )
        return result.scalars().all()


async def get_available_countries():
    async with async_session() as session:
        result = await session.execute(select(Config.country).distinct())
        return result.scalars().all()


async def get_all_configs():
    async with async_session() as session:
        result = await session.execute(select(Config))
        rows = result.scalars().all()
        print(f"   🔍 DB_DEBUG: Found {len(rows)} configs in database.")
        return rows


async def get_configs_by_country_tiered(country_code: str, limit: int):
    async with async_session() as session:
        result = await session.execute(
            select(Config)
            .where(Config.country == country_code)
            .order_by(Config.tier.asc(), Config.ping.asc())
            .limit(limit)
        )
        return result.scalars().all()


async def save_configs_bulk(configs_data: list[dict]):
    if not configs_data:
        return

    async with async_session() as session:
        stmt = pg_insert(Config).on_conflict_do_nothing(index_elements=["uuid"])

        await session.execute(stmt, configs_data)

        await session.commit()

async def get_configs_for_singbox(max_ping=200, min_tier=3, countries=None, limit=10):
    """Получает конфиги для Sing-Box builder."""
    async with async_session() as session:
        query = select(Config).where(Config.is_active == True)
        
        query = query.where(Config.ping <= max_ping)
        query = query.where(Config.tier <= min_tier)
        
        if countries:
            query = query.where(Config.country.in_(countries))
        
        query = query.order_by(Config.tier, Config.ping).limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
async def get_top_configs_for_singbox(limit=30):
    """Лучшие конфиги для Sing-Box — все страны, сортировка по tier+ping."""
    async with async_session() as session:
        query = (
            select(Config)
            .where(Config.is_active == True)
            .order_by(Config.tier, Config.ping)
            .limit(limit)
        )
        result = await session.execute(query)
        return result.scalars().all()
