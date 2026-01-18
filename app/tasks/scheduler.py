import asyncio
import ctypes
import gc
from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.storage import storage
from app.tasks.pipeline.export import run_export, run_whitelist_export
from app.tasks.pipeline.fetch import run_fetch
from app.tasks.pipeline.scan import run_scan

# Попытка загрузить libc
try:
    libc = ctypes.CDLL("libc.so.6")
except Exception:
    libc = None


def deep_clean():
    # 1. Сбор циклических ссылок Python
    gc.collect()
    # 2. Возврат страниц памяти операционной системе
    if libc:
        libc.malloc_trim(0)


async def memory_cleaner():
    deep_clean()


async def update_subscriptions():
    try:
        print("🏁 PIPELINE STARTED")

        await run_fetch()
        deep_clean()  # Чистим после тяжелой загрузки

        await run_scan()
        deep_clean()  # Чистим после создания тысяч задач

        await run_export()
        deep_clean()

        await run_whitelist_export()
        deep_clean()

        moscow_tz = pytz.timezone("Europe/Moscow")
        current_time = datetime.now(moscow_tz).strftime("%H:%M %d.%m")

        storage.set_last_update(current_time)

        print(f"✅ CYCLE COMPLETE: {current_time}")
    except Exception as e:
        print(f"❌ PIPELINE ERROR: {e}")
        import traceback

        traceback.print_exc()
        deep_clean()  # Чистим даже при ошибке


def start_scheduler():
    scheduler = AsyncIOScheduler()

    # Основной цикл обновлений
    scheduler.add_job(update_subscriptions, "interval", minutes=20)

    scheduler.add_job(memory_cleaner, "interval", minutes=5)

    scheduler.start()
    print("Scheduler started.")
