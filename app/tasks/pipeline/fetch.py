import asyncio
import gc

import aiohttp

from app.utils.parser import get_vless_info, parse_links
from config import SUBSCRIPTION_SOURCES
from database.methods import clear_raw_table, save_raw_batch


async def run_fetch():
    print("PIPELINE: Step 1 - Fetching...")
    await clear_raw_table()

    # TCP Connector с лимитом соединений (защита от краша)
    conn = aiohttp.TCPConnector(limit=15, ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        sources = list(SUBSCRIPTION_SOURCES.items())
        # Грузим по 3 источника за раз, чтобы не забить память текстом
        chunk_size = 3
        for i in range(0, len(sources), chunk_size):
            tasks = [
                process_source(session, name, url)
                for name, url in sources[i : i + chunk_size]
            ]
            await asyncio.gather(*tasks)
            gc.collect()

    print("PIPELINE: Fetch done.")


async def process_source(session, name, url):
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                return
            content = await resp.read()
            text = content.decode("utf-8", errors="ignore")
            del content

            links = parse_links(text)
            del text
            if not links:
                return

            seen, unique = set(), []
            for link in links:
                info = get_vless_info(link)
                if not info:
                    continue
                sig = f"{info.host}:{info.port}"
                if sig not in seen:
                    seen.add(sig)
                    unique.append({"full_link": link, "source": name})

            if unique:
                await save_raw_batch(unique)
                print(f"{name}: {len(unique)} saved")
    except Exception as e:
        print(f"Err {name}: {e}")
