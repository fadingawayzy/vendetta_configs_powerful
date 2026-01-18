from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN

default = DefaultBotProperties(parse_mode=ParseMode.HTML)

# BOT_TOKEN теперь гарантированно str, ошибка исчезнет
bot = Bot(token=BOT_TOKEN, default=default)

dp = Dispatcher(storage=MemoryStorage())
