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
RAM_LIMIT = float(os.getenv("RAM_LIMIT_MB", "180"))  # 1 ГБ

# Подключаем ручное управление памятью Linux (просто библиотеку чтобы работать с ЯП C и в целом его методами/функциями не ебу короче )
try:
    libc_path = ctypes.util.find_library("c")
    libc = ctypes.CDLL(libc_path)
except Exception:
    libc = None


def force_release_memory():
    #обычная очистка памяти
    gc.collect()
    # используем корректное имя метода очистки кэша интерпретатора
    # чистим всю память которая осталась у интерпретатора 
    if hasattr(sys, "_clear_type_cache"):
        sys._clear_type_cache()
    # забираем вообще всё у аллокатора malloc
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
            print(
                f"📊 {rss/RAM_LIMIT*100} RAM: {rss:.1f}/{RAM_LIMIT}MB | "
                f"{cpu} CPU: {cpu:.1f}%",
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
