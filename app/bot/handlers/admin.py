import io
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from config import ADMIN_PASSWORD
from app.bot.middlewares.logger import MEMORY_LOGS

router = Router()

@router.message(F.text == ADMIN_PASSWORD)
async def get_logs_handler(message: Message):
    # LOCAL IMPORT для предотвращения циклической зависимости
    # admin -> scheduler -> fetch -> ...
    from app.tasks.scheduler import update_subscriptions
    
    # Если лог пуст
    if not MEMORY_LOGS:
        await message.answer("📭 Лог пуст.")
        return

    # Собираем логи
    logs_text = "".join(MEMORY_LOGS)
    file_in_memory = io.BytesIO(logs_text.encode('utf-8'))
    document = BufferedInputFile(file_in_memory.getvalue(), filename="logs_history.txt")

    await message.answer_document(
        document,
        caption="🕵️‍♂️ <b>Логи сессии</b>"
    )