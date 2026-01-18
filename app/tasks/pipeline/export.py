import asyncio
import base64
import re

import aiohttp

from app.utils.github import update_gist
from config import config
from database.methods import get_all_configs


def extract_gist_id(url: str) -> str:
    match = re.search(r"githubusercontent\.com/[^/]+/([^/]+)/raw", url)
    return match.group(1) if match else None


async def run_export():
    print("🚀 PIPELINE: Step 3 - Export...", flush=True)

    # 1. Берем живые конфиги из базы
    configs = await get_all_configs()

    if not configs:
        print("⚠️ No configs to export.")
        return

    # 2. Сортируем (быстрые - вверх)
    configs.sort(key=lambda x: x.ping)

    # 3. Берем Топ-300
    top_list = [c.link for c in configs[:1000]]

    # 4. Заливаем
    slots = list(config.GIST_SLOTS.items())
    total_slots = len(slots)

    if total_slots == 0:
        return

    chunk = len(top_list) // total_slots

    for i, (name, url) in enumerate(slots):
        start = i * chunk
        end = start + chunk
        if i == total_slots - 1:
            end = len(top_list)

        part = top_list[start:end]
        if not part:
            continue

        text = "\n".join(part)
        b64_content = base64.b64encode(text.encode()).decode()

        gist_id = extract_gist_id(url)
        if gist_id:
            filename = f"sub.txt"  # Имя файла в гисте
            success = await update_gist(gist_id, filename, b64_content)
            st = "OK" if success else "ERR"
            print(f"{name}: {st}", flush=True)
        else:
            print(f"{name}: Invalid URL", flush=True)

    print("PIPELINE: Export done.", flush=True)


async def run_whitelist_export():
    print("WHITELIST: Lazy Export started...")

    slots_map = {6: "Mobile", 7: "SNI"}  # Слот 6 берет Mobile CIDR  # Слот 7 берет SNI

    # Gist_URL
    gist_slots = config.GIST_SLOTS

    for slot_num, source_key in slots_map.items():
        slot_key = f"SLOT_{slot_num}"

        # Получаем URL источника и наш Gist
        source_url = config.WHITELIST_SOURCES.get(source_key)
        gist_url = gist_slots.get(slot_key)

        if not source_url or not gist_url:
            print(f"Whitelist: Missing config for {slot_key}")
            continue

        try:
            # 2. Скачиваем текст из репозитория
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url, timeout=10) as resp:
                    if resp.status != 200:
                        print(
                            f"❌ Whitelist: Failed to fetch {source_key} ({resp.status})"
                        )
                        continue
                    raw_text = await resp.text()

            def encode_data(text):
                return base64.b64encode(text.encode("utf-8")).decode("utf-8")

            b64_content = await asyncio.to_thread(encode_data, raw_text)
            del raw_text

            # Заливаем в наш Gist
            gist_id = extract_gist_id(gist_url)
            if gist_id:
                success = await update_gist(gist_id, "sub.txt", b64_content)
                status = "OK" if success else "ERR"
                print(f"   [{slot_key} ({source_key})]: {status}")
            else:
                print(f"   [{slot_key}]: Invalid Gist URL")

        except Exception as e:
            print(f"   [{slot_key}] Error: {e}")

    print("WHITELIST: Export finished.")
