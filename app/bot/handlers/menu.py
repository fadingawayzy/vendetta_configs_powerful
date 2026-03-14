import gc
import io
import urllib.parse

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.utils.singbox_builder import build_for_profile, PROFILES
from database.methods import get_configs_for_singbox
from app.bot.keyboards.main_kb import get_inline_menu
from app.bot.keyboards.sub_kb import (
    get_back_to_my_json,
    get_back_to_my_qr,
    get_back_to_share_kb,
    get_back_to_subs_kb,
    get_countries_kb,
    get_custom_link_kb,
    get_custom_sub_kb,
    get_lucky_kb,
    get_share_kb,
    get_slot_selection_kb,
    get_sub_menu_kb,
)
from app.bot.states import CustomSubFlow
from app.core.storage import storage
from app.utils.qr_generator import generate_single_qr
from config import config
from database.methods import (
    get_user_settings,
    get_user_slot,
    set_user_filter,
    set_user_limit,
    set_user_slot,
)

router = Router()

DISCLAIMER = (
    "\n⚠️ <i>Тестовый режим. Конфиги генерируются на лету. "
    "Для 100% стабильности используйте «Вечную подписку».</i>"
)
CUSTOM_WARN = (
    "\n\n⚠️ <i>Внимание: В подписку попадут только те страны, для которых сейчас найдены "
    "живые серверы. Если серверов нет, страна будет пропущена.</i>"
)

# --- ГЛАВНОЕ МЕНЮ ---


@router.callback_query(F.data == "main_menu")
async def cb_main(call: CallbackQuery):
    last_upd = storage.last_update
    text = (
        f"🤖 <b>Панель управления</b>\n🔄 Обновлено: {last_upd}\n\n"
        f"⚠️ Важно: Бот собирает бесплатные ключи из открытых источников.\n"
        f"Самые быстрые в разделе <b>'Моя подписка'</b>."
    )
    kb = get_inline_menu()
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.delete()
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")




@router.callback_query(F.data == "subs_menu")
async def cb_show_subscription(call: CallbackQuery):
    user_id = call.from_user.id
    slot_num = await get_user_slot(user_id)

    disclaimer = ""
    if slot_num in [6, 7]:
        disclaimer = "\n\n⚠️ <b>Внимание: Слот 6 и 7 (для белых списков)- тестовые.</b>"

    if slot_num == 0:
        sub_url = f"{config.APP_BASE_URL}/sub/{user_id}"
        slot_name = "Собственный сет 🛠"
    else:
        slot_key = f"SLOT_{slot_num}"
        sub_url = config.GIST_SLOTS.get(slot_key, "Error")
        slot_name = f"Слот {slot_num}"

    text = (
        f"♾ <b>Ваша вечная подписка ({slot_name})</b>\n\n"
        f"<code>{sub_url}</code>\n\n"
        f"<i>💡 Обновляется каждые 20 минут.</i>"
        f"{disclaimer}"
    )
    kb = get_sub_menu_kb(sub_url)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.delete()
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "change_slot_menu")
async def cb_change_slot_menu(call: CallbackQuery):
    await call.message.edit_text(
        text="🔄 <b>Выберите слот подписки</b>",
        reply_markup=get_slot_selection_kb(config.GIST_SLOTS),
    )


@router.callback_query(F.data.startswith("set_slot_"))
async def cb_set_slot(call: CallbackQuery):
    new_slot = int(call.data.split("_")[-1])
    user_id = call.from_user.id
    if new_slot == 0:
        countries, _ = await get_user_settings(user_id)
        if not countries:
            await call.answer("⚠️ Сначала настройте сет!", show_alert=True)
            return
    await set_user_slot(user_id, new_slot)
    await call.answer(f"✅ Выбран слот {new_slot}")
    await cb_show_subscription(call)




@router.callback_query(F.data == "country_menu")
async def cb_countries(call: CallbackQuery):
    kb = await get_countries_kb()
    await call.message.edit_text(
        "🌍 <b>Выберите страну:</b>", reply_markup=kb, parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("country_"))
async def cb_country_select(call: CallbackQuery):
    code = call.data.split("_")[1]
    configs = await storage.get_best(code, limit=3)
    if not configs:
        await call.answer("Пусто :(", show_alert=True)
        return
    text = f"🌍 <b>Топ серверов: {code}</b>\n\n"
    for c in configs:
        link = c.get("full_link", "Error")
        text += f"{c.get('flag')} | ⚡️ {c.get('ping')}ms\n<code>{link}</code>\n\n"

    b = InlineKeyboardBuilder()
    b.button(text="🔙 К выбору стран", callback_data="country_menu")
    await call.message.edit_text(
        text + DISCLAIMER, reply_markup=b.as_markup(), parse_mode="HTML"
    )




@router.callback_query(F.data.in_({"lucky", "lucky_reroll"}))
async def cb_lucky(call: CallbackQuery):
    configs = await storage.get_random_best(limit=1)
    if not configs:
        await call.answer("⚠️ База пуста", show_alert=True)
        return
    c = configs[0]
    text = (
        f"🎲 <b>Мне повезет!</b>\n"
        f"{c.get('flag')} {c.get('country')} | ⚡️ {c.get('ping')}ms\n"
        f"<code>{c.get('full_link')}</code>{DISCLAIMER}"
    )
    try:
        await call.message.edit_text(
            text, reply_markup=get_lucky_kb(), parse_mode="HTML"
        )
    except:
        await call.message.answer(text, reply_markup=get_lucky_kb(), parse_mode="HTML")




@router.callback_query(F.data == "share_menu")
async def cb_share_menu(call: CallbackQuery):
    share_text = "🚀VPN от Vendetta Configs\nBot: @vendettaconfigs_bot"
    kb = get_share_kb(urllib.parse.quote(share_text))
    await call.message.delete()
    await call.message.answer(
        "🤝 <b>Поделись скоростью!</b>", reply_markup=kb, parse_mode="HTML"
    )


@router.callback_query(F.data == "share_qr")
async def cb_share_qr(call: CallbackQuery):
    await _send_qr(call, "QR Слот", get_back_to_share_kb())




@router.callback_query(F.data == "sub_qr")
async def cb_sub_qr(call: CallbackQuery):
    await _send_qr(call, "🔳 Ваш QR-код", get_back_to_my_qr())


@router.callback_query(F.data == "custom_qr")
async def cb_custom_qr(call: CallbackQuery):
    await _send_qr(call, "🔳 QR (Custom)", get_back_to_subs_kb())


async def _send_qr(call: CallbackQuery, caption: str, kb):
    """Универсальная функция отправки QR с жестким контролем памяти."""
    user_id = call.from_user.id
    slot_num = await get_user_slot(user_id)

    # Определяем URL
    if slot_num == 0:
        url = f"{config.APP_BASE_URL}/sub/{user_id}"
    else:
        url = config.GIST_SLOTS.get(f"SLOT_{slot_num}", "Error")

    await call.answer("Генерирую QR...")

    # 1. Генерация
    bio = await generate_single_qr(url)

    # 2. Создание объекта InputFile
    photo = BufferedInputFile(bio.getvalue(), filename="qr.png")

    try:
        # 3. Отправка (Удаляем прошлое, шлем новое, чтобы не мигало)
        await call.message.delete()
        await call.message.answer_photo(photo, caption=caption, reply_markup=kb)
    finally:
        # 4. ЯВНАЯ ОЧИСТКА
        bio.close()
        del bio
        del photo
        gc.collect()  # Чистим после отправки файла (aiogram может кэшировать)


@router.callback_query(F.data == "sub_json")
async def cb_sub_json(call: CallbackQuery):
    await _send_json(call, "subscription.json", get_back_to_my_json())


@router.callback_query(F.data == "custom_json")
async def cb_custom_json(call: CallbackQuery):
    await _send_json(call, "custom_config.json", get_back_to_subs_kb())


async def _send_json(call: CallbackQuery, filename: str, kb):
    """Универсальная отправка JSON с контролем памяти."""
    user_id = call.from_user.id
    slot_num = await get_user_slot(user_id)

    if slot_num == 0:
        url = f"{config.APP_BASE_URL}/sub/{user_id}"
    else:
        url = config.GIST_SLOTS.get(f"SLOT_{slot_num}", "Error")

    content_str = f'{{"subscribe_url": "{url}", "tag": "Vendetta"}}'

    # Работа с памятью
    bio = io.BytesIO(content_str.encode())
    doc = BufferedInputFile(bio.getvalue(), filename=filename)

    try:
        await call.message.delete()
        await call.message.answer_document(doc, caption="🗂 Конфиг", reply_markup=kb)
    finally:
        # Очистка
        bio.close()
        del bio
        del doc
        del content_str
        gc.collect()



@router.callback_query(F.data == "custom_sub_start")
async def cb_custom_start(call: CallbackQuery, state: FSMContext):
    _, limit = await get_user_settings(call.from_user.id)
    await call.message.edit_text(
        f"🛠 <b>Настройка</b>\nВведите лимит (1-50).\nТекущий: {limit}\n{CUSTOM_WARN}",
        parse_mode="HTML",
    )
    await state.set_state(CustomSubFlow.waiting_limit)
    await call.answer()


@router.message(CustomSubFlow.waiting_limit)
async def msg_set_limit(message: Message, state: FSMContext):
    try:
        limit = int(message.text)
        if not (1 <= limit <= 100):
            raise ValueError

        await set_user_limit(message.from_user.id, limit)
        countries, _ = await get_user_settings(message.from_user.id)
        kb = await get_custom_sub_kb(countries)

        await message.answer(f"✅ Лимит: {limit}. Выберите страны:", reply_markup=kb)
        await state.clear()
    except ValueError:
        await message.answer("❌ Число от 1 до 100.")


@router.callback_query(F.data.startswith("toggle_country_"))
async def cb_toggle_country(call: CallbackQuery):
    code = call.data.split("_")[-1]
    user_id = call.from_user.id
    curr, _ = await get_user_settings(user_id)

    if not curr:
        curr = []  # Защита от None

    if code in curr:
        curr.remove(code)
    else:
        curr.append(code)

    await set_user_filter(user_id, curr)
    await call.message.edit_reply_markup(reply_markup=await get_custom_sub_kb(curr))


@router.callback_query(F.data == "save_custom_sub")
async def cb_save_custom(call: CallbackQuery):
    user_id = call.from_user.id
    await set_user_slot(user_id, 0)
    link = f"{config.APP_BASE_URL}/sub/{user_id}"
    await call.message.edit_text(
        f"✅ <b>Сохранено!</b>\nСсылка:\n<code>{link}</code>",
        reply_markup=get_custom_link_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "clear_custom_countries")
async def cb_clear_countries(call: CallbackQuery):
    await set_user_filter(call.from_user.id, [])
    await call.message.edit_reply_markup(reply_markup=await get_custom_sub_kb([]))
    await call.answer("Очищено")

# === SING-BOX ПРОФИЛИ ===

@router.callback_query(F.data == "singbox_menu")
async def cb_singbox_menu(call: CallbackQuery):
    b = InlineKeyboardBuilder()
    for key, profile in PROFILES.items():
        b.button(text=f"{profile['name']}", callback_data=f"singbox_{key}")
    b.button(text="🔙 Назад", callback_data="main_menu")
    b.adjust(2)
    
    await call.message.edit_text(
        "📱 <b>Sing-Box конфиги</b>\n\n"
        "Выберите профиль. Конфиг включает:\n"
        "• Авто-переключение на быстрый сервер\n"
        "• Банки и Госуслуги работают без VPN\n"
        "• Реклама заблокирована\n"
        "• Kill Switch",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("singbox_"))
async def cb_singbox_profile(call: CallbackQuery):
    profile_name = call.data.replace("singbox_", "")
    profile = PROFILES.get(profile_name)

    if not profile:
        await call.answer("Профиль не найден", show_alert=True)
        return

    user_id = call.from_user.id
    base_url = config.APP_BASE_URL

    if profile_name == "balanced":
        url = f"{base_url}/singbox/{user_id}"
    else:
        url = f"{base_url}/singbox/{user_id}/{profile_name}"

    b = InlineKeyboardBuilder()
    b.button(text="🔄 Другой профиль", callback_data="singbox_menu")
    b.button(text="🔙 Меню", callback_data="main_menu")
    b.adjust(2)

    await call.message.edit_text(
        f"📱 <b>{profile['name']}</b>\n"
        f"{profile['description']}\n\n"
        f"<b>Ссылка подписки:</b>\n"
        f"<code>{url}</code>\n\n"
        f"<b>Как подключить:</b>\n"
        f"1. Скачай <b>Hiddify</b> из Google Play / App Store\n"
        f"2. Скопируй ссылку выше\n"
        f"3. В Hiddify нажми + → Добавить из буфера\n"
        f"4. Включи — готово!\n\n"
        f"🇷🇺 Сбер, Госуслуги, Яндекс — напрямую\n"
        f"🌍 YouTube, Discord, Instagram — через VPN\n"
        f"🚫 Реклама заблокирована\n"
        f"⚡ Авто-переключение на быстрый сервер",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )