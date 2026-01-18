from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from app.bot.keyboards.main_kb import get_main_menu, get_inline_menu
from app.core.storage import storage

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Это бот для получения подписок, сформированных из бесплатных VLESS конфигураций по открытым источникам.\n"
        "Нажми кнопку ниже, чтобы открыть меню.",
        reply_markup=get_main_menu()
    )
    await show_menu(message)

@router.message(F.text == "🚀 Меню")
async def msg_menu(message: Message):
    await show_menu(message)

async def show_menu(message: Message):
    # берем время обновления из стореджа
    disclaimer_2 = "⚠️ Важно: Бот собирает бесплатные ключи из открытых источников, поэтому они могут быть нестабильны.\n\nСамые быстрые и стабильные можно найти в разделе <b>'Моя подписка'</b>."
    last_upd = storage.last_update
    await message.answer(
        f"🤖 <b>Панель управления</b>\n"
        f"🔄 База обновлена: <b>{last_upd}</b>\n\n"
        f"{disclaimer_2}\n\n",
        reply_markup=get_inline_menu(),
        parse_mode = "HTML"
    )
