from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Меню")]
        ],
        resize_keyboard=True,
        persistent=True
    )


def get_inline_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="♾ Моя Подписка", callback_data="subs_menu")

    builder.button(text="🌍 Выбор страны", callback_data="country_menu")

    builder.button(text="📚 FAQ / Помощь", url="https://telegra.ph/Instrukciya-po-podklyucheniyu-VPN-cherez-VLESS-01-11")

    builder.button(text="🎲 Мне повезет", callback_data="lucky")

    builder.button(text="🤝 Поделиться", callback_data="share_menu")

    builder.button(text="📱 Sing-Box", callback_data="singbox_menu")
    builder.adjust(1)
    return builder.as_markup()
