import asyncio

from app.bot.handlers import admin, menu, start
from app.bot.middlewares.logger import UserActivityLogger
from app.loader import bot as telegram_bot
from app.loader import dp
from app.tasks.scheduler import start_scheduler, update_subscriptions
from app.utils.web_server import start_web_server


async def start_app():
    print("🚀 STARTUP: Инициализация...", flush=True)

    # 1. Роутеры
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(admin.router)
    dp.update.outer_middleware(UserActivityLogger())

    # 2. Веб-сервер (С таймаутом, чтобы не повесить старт)
    print("🌐 WEB-SERVER: Starting...", flush=True)
    web_runner = None
    try:
        web_runner = await asyncio.wait_for(start_web_server(), timeout=30)
        print("✅ WEB-SERVER: OK", flush=True)
    except Exception as e:
        import traceback

        print(f"⚠️ WEB-SERVER FAILED: {e} (Bot will continue)", flush=True)
        traceback.print_exc()
    # 3. Планировщик (Scheduler)
    start_scheduler()

    # 4. Telegram Webhook (Очистка)
    print("🔄 TELEGRAM: Clearing webhook...", flush=True)
    try:
        await telegram_bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print(f"⚠️ TELEGRAM ERROR: {e}", flush=True)

    # 5. СТАРТ ОБНОВЛЕНИЯ БАЗЫ (В фоне!)
    # create_task гарантирует, что эта задача пойдет в параллельный поток
    # и не заблокирует start_polling. Бот ответит мгновенно.
    print("🔄 DATABASE: Starting background update...", flush=True)
    asyncio.create_task(update_subscriptions())

    # 6. Polling
    print("✅ BOT STARTED: Ready!", flush=True)
    try:
        await dp.start_polling(telegram_bot)
    finally:
        if web_runner:
            await web_runner.cleanup()
