from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Добавляем импорты для кастомного сервера:
from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN

# 1. Твоя ссылка на Cloudflare Worker
CUSTOM_API_URL = "https://vendetta-bot.paricdavidccc.workers.dev"

# 2. Создаем кастомный сервер и прокидываем его в сессию
custom_server = TelegramAPIServer.from_base(CUSTOM_API_URL)
session = AiohttpSession(api=custom_server)

default = DefaultBotProperties(parse_mode=ParseMode.HTML)

# 3. Инициализируем бота с нашей кастомной сессией
# Обязательно оставляем твой default=default
bot = Bot(token=BOT_TOKEN, default=default, session=session)

dp = Dispatcher(storage=MemoryStorage())
