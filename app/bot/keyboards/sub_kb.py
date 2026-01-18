from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from app.core.storage import storage
from database.methods import get_available_countries



async def get_countries_kb():
    builder = InlineKeyboardBuilder()
    
    
    countries = await storage.get_countries() 
    
    for code in countries:
        flag = chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)
        builder.button(text=f"{flag} {code}", callback_data=f"country_{code}")
        
    builder.button(text="🔙 Назад", callback_data="main_menu")
    builder.adjust(3)
    return builder.as_markup()




def get_sub_menu_kb(current_url: str):
    # клавиатура управления подпиской
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Сменить подписку", callback_data="change_slot_menu")
    builder.button(text="🔳 QR-код", callback_data="sub_qr")
    builder.button(text="🗂 Скачать JSON", callback_data="sub_json")
    builder.button(text="🔙 В главное меню", callback_data="main_menu")
    builder.adjust(1, 2, 1)
    return builder.as_markup()


def get_slot_selection_kb(slots: dict):
    builder = InlineKeyboardBuilder()

    # 1. Обычные слоты (1-5) из конфига
    for name in slots.keys():
        if name.startswith("SLOT"):
            slot_num = name.split("_")[-1]
            num = int(slot_num)
            if num <= 5:
                builder.button(text=f"📦 Слот {num}", callback_data=f"set_slot_{num}")

    # специальные слоты (6 и 7)
    builder.button(text="📱 Слот 6 CIDR (Белые списки, мобильный интернет)", callback_data="set_slot_6")
    builder.button(text="🌐 Слот 7 SNI (Белые списки, мобильный интернет)", callback_data="set_slot_7")

    builder.button(text="🛠 Мой собственный сет", callback_data="set_slot_0")
    builder.button(text="⚙️ Настроить собственный сет", callback_data="custom_sub_start")
    builder.button(text="🔙 Отмена", callback_data="subs_menu")

    builder.adjust(2, 2, 1, 2, 1, 1, 1, 1)
    return builder.as_markup()


def get_faq_kb():
    # кнопка возврата из faq
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад к подписке", callback_data="subs_menu")
    return builder.as_markup()

def get_lucky_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="😭 Мне не повезло!", callback_data="lucky_reroll")
    builder.button(text="🔙 В меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


# поделиться

def get_share_kb(share_text: str):
    builder = InlineKeyboardBuilder()

    share_url = f"https://t.me/share/url?url={share_text}"
    builder.button(text="📨 Отправить другу", url=share_url)

    builder.button(text="🔳 Показать QR-код", callback_data="share_qr")
    builder.button(text="🔙 В меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_back_to_share_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="share_menu")

    return builder.as_markup()

def get_back_to_my_qr():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="subs_menu")

    return builder.as_markup()

def get_back_to_my_json():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="subs_menu")

    return builder.as_markup()


async def get_custom_sub_kb(selected_countries: list[str]):
    builder = InlineKeyboardBuilder()
    all_countries = await get_available_countries()
    EXCLUDED = {'RU', 'UNK', 'BY'}
    clean_countries = sorted([c for c in all_countries if c not in EXCLUDED])
    
    for code in clean_countries:
        flag = chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)
        if code in selected_countries:
            text = f"✅ {flag} {code}"
        else:
            text = f"{flag} {code}"
        builder.button(text=text, callback_data=f"toggle_country_{code}")
    #кнопка сброса всех флагов
    builder.row(
        InlineKeyboardButton(text="🗑 Сбросить всё", callback_data="clear_custom_countries")
    )
    # Кнопки сохранения
    builder.row(
        InlineKeyboardButton(text="💾 Сохранить", callback_data="save_custom_sub"),
        InlineKeyboardButton(text="🔙 Отмена", callback_data="subs_menu")
    )
    
    builder.adjust(3)
    return builder.as_markup()

def get_custom_link_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔳 QR-код", callback_data="custom_qr")
    builder.button(text="🗂 JSON", callback_data="custom_json")
    builder.button(text="🔙 В меню", callback_data="subs_menu")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_back_to_subs_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад к подписке", callback_data="subs_menu")
    return builder.as_markup()







