import asyncio
import ctypes
import logging
import os
import sys

import psutil

from database.connection import init_models

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import start_app

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Разгон под мощный сервер
CPU_LIMIT = 1.0
RAM_LIMIT = 1024.0

try:
    libc = ctypes.CDLL("libc.so.6")
except Exception:
    libc = None


async def resource_monitor():
    """Монитор для 1-ядерного сервера (1.0 CPU / 1024MB RAM)"""
    process = psutil.Process(os.getpid())
    LIMIT_CPU = 100.0  # 100% одного ядра
    LIMIT_RAM = 1024.0

    process.cpu_percent(None)  # Init
    print(f"🖥️  SYSTEM: Mode 1-Core / {LIMIT_RAM}MB RAM", flush=True)

    while True:
        await asyncio.sleep(60)
        try:
            # 1. Сбор данных
            rss = process.memory_info().rss / 1024 / 1024

            # 2. CPU: На 1 ядре это значение прямо показывает нагрузку в %
            cpu_usage = process.cpu_percent(None)

            # 3. Визуализация
            def make_bar(p):
                # Ограничиваем шкалу 100%, чтобы не вылетала за границы
                p_norm = max(0, min(100, p))
                filled = int(p_norm / 10)
                return "[" + "█" * filled + "░" * (10 - filled) + "]"

            # Вывод лога
            # Если нагрузка > 90%, пишем WARNING
            status_prefix = "⚠️" if cpu_usage > 90 else "📊"

            print(
                f"{status_prefix} {make_bar(rss/LIMIT_RAM*100)} RAM: {rss:.1f}/{LIMIT_RAM}MB | "
                f"{make_bar(cpu_usage)} CPU: {cpu_usage:.1f}%",
                flush=True,
            )

            # Радикальное освобождение памяти 
            if libc:
                libc.malloc_trim(0)
        except:
            pass


async def main():
    print("🚀 ENGINE START...", flush=True)
    try:
        await init_models()
        print("📦 DB: OK", flush=True)
    except Exception as e:
        print(f"❌ DB ERROR: {e}", flush=True)

    asyncio.create_task(resource_monitor())
    await start_app()


if __name__ == "__main__":
    # Включаем UVLOOP для бешеной скорости ввода-вывода
    try:
        import uvloop

        uvloop.install()
        print("⚡ UVLOOP: ENABLED")
    except ImportError:
        print("⚠️ UVLOOP: Not found (Using standard)")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
