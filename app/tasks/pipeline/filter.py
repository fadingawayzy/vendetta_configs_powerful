import asyncio
import gc

from app.utils.geo import get_country
from app.utils.parser import get_vless_info  # Оставляем get_vless_info для парсинга
from database.methods import count_raw_configs, get_raw_batch

GEO_SEM = asyncio.Semaphore(50)  # было 10


async def async_get_country_safe(host):
    async with GEO_SEM:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, get_country, host)


async def get_filtered_candidates(batch_size=500):

    total = await count_raw_configs()
    if total == 0:
        return

    offset = 0
    buffer = []
    READ_SIZE = 1000

    while offset < total:
        # raw_rows - это список объектов RawConfig, у них есть .full_link
        raw_rows = await get_raw_batch(limit=READ_SIZE, offset=offset)
        if not raw_rows:
            break

        tasks = []
        meta_data = []

        for row in raw_rows:
            # Парсим ссылку из row.full_link
            info = get_vless_info(row.full_link)
            if not info:
                continue

            if info.security not in ["reality", "tls"]:
                continue

            tasks.append(async_get_country_safe(info.host))
            # Сохраняем и info, и исходную ссылку
            meta_data.append(
                {"info": info, "source": row.source, "original_link": row.full_link}
            )

        if tasks:
            results = await asyncio.gather(*tasks)

            for meta_item, geo_result in zip(meta_data, results):
                if not geo_result:
                    continue
                code, flag = geo_result

                if code in ["RU", "UNK", "CN", "IR", "KP"]:
                    continue

                # Добавляем в буфер СЛОВАРЬ
                buffer.append(
                    {
                        "info": meta_item["info"],  # Объект VlessInfo
                        "country": code,
                        "flag": flag,
                        "source": meta_item["source"],
                        "original_link": meta_item[
                            "original_link"
                        ],  # Явно передаем ссылку
                    }
                )

        while len(buffer) >= batch_size:
            chunk = buffer[:batch_size]
            buffer = buffer[batch_size:]
            yield chunk
            del chunk

        offset += READ_SIZE
        del raw_rows, tasks, meta_data, results
        gc.collect()

    if buffer:
        yield buffer
        del buffer
        gc.collect()
