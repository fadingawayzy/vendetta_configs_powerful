import asyncio
import ctypes
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

# Подключаем ручное управление памятью Linux
try:
    libc = ctypes.CDLL("libc.so.6")
except Exception:
    libc = None

def force_release_memory():
    if libc:
        libc.malloc_trim(0)

async def silent_memory_cleaner():
    while True:
        await asyncio.sleep(60)
        force_release_memory()

async def main():
    print("🎬 STARTING: Запуск системы...", flush=True)
    
    # 1. Подключение к БД
    try:
        await init_models()
        print("📦 DATABASE: OK", flush=True)
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}", flush=True)
    
    # 2. Запуск фоновой очистки памяти (без логов)
    asyncio.create_task(silent_memory_cleaner())
    
    # 3. Запуск бота и веб-сервера
    await start_app()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass