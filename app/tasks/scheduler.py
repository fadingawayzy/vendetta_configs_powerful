import asyncio
import ctypes
import ctypes.util
import gc
import sys
from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.storage import storage
from app.tasks.pipeline.export import run_export, run_whitelist_export
from app.tasks.pipeline.fetch import run_fetch
from app.tasks.pipeline.scan import run_scan

# Безопасная загрузка библиотеки C
try:
    libc_path = ctypes.util.find_library("c")
    libc = ctypes.CDLL(libc_path)
except Exception:
    libc = None


def deep_clean():
    """Глубокая очистка памяти после тяжелых задач."""
    gc.collect()
    sys._clear_internal_caches()
    if libc and hasattr(libc, "malloc_trim"):
        try:
            libc.malloc_trim(0)
        except Exception:
            pass


async def memory_cleaner():
    """Задача очистки по расписанию."""
    deep_clean()


async def update_subscriptions():
    """Полный цикл обновления базы."""
    try:
        print("🏁 PIPELINE STARTED")

        await run_fetch()
        deep_clean()

        await run_scan()
        deep_clean()

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
        deep_clean()


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_subscriptions, "interval", minutes=20)
    scheduler.add_job(memory_cleaner, "interval", minutes=5)
    scheduler.start()
    print("Scheduler started.")
