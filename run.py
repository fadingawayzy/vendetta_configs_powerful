import asyncio
import ctypes
import ctypes.util
import gc
import logging
import os
import sys

import psutil

from database.connection import init_models

# Добавляем корень проекта в пути поиска модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import start_app

# Оставляем только системные уведомления уровня INFO
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

CPU_LIMIT = 100.0  # 1 ядро
RAM_LIMIT = 1024.0  # 1 ГБ

# Подключаем ручное управление памятью Linux
try:
    libc_path = ctypes.util.find_library("c")
    libc = ctypes.CDLL(libc_path)
except Exception:
    libc = None


def force_release_memory():
    """Радикальная очистка памяти."""
    gc.collect()
    # ИСПРАВЛЕНО: корректное имя метода очистки кэша интерпретатора
    if hasattr(sys, "_clear_type_cache"):
        sys._clear_type_cache()

    if libc and hasattr(libc, "malloc_trim"):
        try:
            libc.malloc_trim(0)
        except Exception:
            pass


async def resource_monitor():
    """Монитор ресурсов с визуализацией."""
    process = psutil.Process(os.getpid())
    process.cpu_percent(None)
    print(f"🖥️  MONITOR: Active (Limit: 1-Core / {RAM_LIMIT}MB RAM)", flush=True)

    while True:
        await asyncio.sleep(60)
        try:
            rss = process.memory_info().rss / 1024 / 1024
            cpu = process.cpu_percent(None)

            def make_bar(p):
                p_norm = max(0, min(100, p))
                filled = int(p_norm / 10)
                return "[" + "█" * filled + "░" * (10 - filled) + "]"

            print(
                f"📊 {make_bar(rss/RAM_LIMIT*100)} RAM: {rss:.1f}/{RAM_LIMIT}MB | "
                f"{make_bar(cpu)} CPU: {cpu:.1f}%",
                flush=True,
            )

            force_release_memory()
        except Exception:
            pass


async def main():
    print("🎬 ENTRY POINT: Запуск...", flush=True)
    try:
        await init_models()
        print("📦 DATABASE: OK", flush=True)
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}", flush=True)

    asyncio.create_task(resource_monitor())
    await start_app()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
