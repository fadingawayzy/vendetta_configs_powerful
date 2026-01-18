import random

from sqlalchemy import func, select

from database.connection import async_session
from database.methods import (
    get_available_countries,
    get_configs_by_country,
    get_user_slot,
    set_user_slot,
)
from database.models.config import Config


class Storage:
    def __init__(self):
        self._last_update = "ожидание..."

    @property
    def last_update(self):
        return self._last_update

    def set_last_update(self, time_str: str):
        self._last_update = time_str

    async def get_user_slot(self, user_id: int) -> int:
        return await get_user_slot(user_id)

    async def set_user_slot(self, user_id: int, slot: int):
        await set_user_slot(user_id, slot)

    async def get_countries(self) -> list[str]:
        raw_countries = await get_available_countries()
        EXCLUDED = {"UA", "RU", "BY", "UNK", "IR", "CN"}
        filtered = [c for c in raw_countries if c and c not in EXCLUDED]
        return sorted(filtered)

    async def get_best(self, country_code: str, limit: int = 3) -> list:
        # Теперь метод возвращает сортированные по Tier, потом Ping
        # Мы просто берем топ-3, это будут лучшие из лучших
        rows = await get_configs_by_country(country_code, limit)
        return [
            {"flag": r.flag, "country": r.country, "ping": r.ping, "full_link": r.link}
            for r in rows
        ]

    async def get_random_best(self, limit: int = 1) -> list:
        async with async_session() as session:
            # Ищем только Tier 1 или 2 для "Мне повезет"
            result = await session.execute(
                select(Config)
                .where(Config.tier <= 2)
                .where(Config.ping < 500)
                .order_by(func.random())
                .limit(limit)
            )
            rows = result.scalars().all()
            return [
                {
                    "flag": r.flag,
                    "country": r.country,
                    "ping": r.ping,
                    "full_link": r.link,
                }
                for r in rows
            ]


storage = Storage()
