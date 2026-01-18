import asyncio
import os
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import Update

LOG_FILE = "user_actions.txt"
MEMORY_LOGS = []
MEMORY_LIMIT = 500


class UserActivityLogger(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        # Максимально безопасное получение пользователя
        user = None
        if event.message:
            user = event.message.from_user
        elif event.callback_query:
            user = event.callback_query.from_user
        elif event.inline_query:
            user = event.inline_query.from_user

        if not user:
            # Если это системный апдейт без юзера, просто пропускаем дальше
            return await handler(event, data)

        # Определение действия
        action = "Unknown"
        try:
            if event.message:
                if event.message.text:
                    action = f"[Text] {event.message.text[:30]}"
                elif event.message.photo:
                    action = "[Photo]"
                else:
                    action = f"[Msg: {event.message.content_type}]"
            elif event.callback_query:
                action = f"[Button] {event.callback_query.data}"
            elif event.inline_query:
                action = f"[Inline] {event.inline_query.query}"
        except Exception:
            action = "Parse Error"

        action = str(action).replace("\n", " ").replace("\r", "")[:50]

        now = datetime.now().strftime("%H:%M:%S")
        safe_name = (user.first_name or "NoName").replace(" ", "_")

        log_line = f"{now} | {user.id} | {safe_name} | {action}"

        # Пишем в консоль (принудительно flush, чтобы видеть сразу)
        print(f"📝 {log_line}", flush=True)

        # Сохраняем в память
        MEMORY_LOGS.append(log_line)
        if len(MEMORY_LOGS) > MEMORY_LIMIT:
            MEMORY_LOGS.pop(0)

        # Пишем в файл асинхронно
        asyncio.create_task(self._async_write(log_line))

        return await handler(event, data)

    async def _async_write(self, content: str):
        """Безопасная запись в файл в отдельном потоке"""
        try:
            await asyncio.to_thread(self._write_to_disk, content)
        except Exception as e:
            print(f"Log Error: {e}")

    def _write_to_disk(self, content: str):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(content + "\n")
