import base64
import re
import urllib.parse
from dataclasses import dataclass
from typing import Optional

# ОПТИМИЗАЦИЯ: Компилируем Regex один раз.
# Используем этот паттерн везде, чтобы не нагружать процессор компиляцией при каждом вызове.
VLESS_PATTERN = re.compile(r"(vless://[a-zA-Z0-9\-]+@[a-zA-Z0-9\.\-\:\[\]]+[^#\s]*)")


# Структура данных оставлена без изменений
@dataclass
class VlessInfo:
    link: str  # полная ссылка
    uuid: str  # пароль
    host: str  # адрес сервера
    port: int  # порт
    security: str  # тип шифрования (reality/tls)
    sni: str  # домен маскировки
    name: str  # название (после #)


def decode_base64(text: str) -> str:
    if not text:
        return ""

    # Быстрая очистка от пробелов
    text = text.strip()

    try:
        # Автоматическое добавление padding для корректного декодирования
        missing_padding = len(text) % 4
        if missing_padding:
            text += "=" * (4 - missing_padding)

        return base64.b64decode(text).decode("utf-8", errors="ignore")
    except Exception:
        # Если не вышло - возвращаем исходный текст (возможно это не base64, а просто список)
        return text


def parse_links(text: str) -> list[str]:
    if not text:
        return []

    # Сначала пробуем расшифровать (если это подписка)
    decoded_text = decode_base64(text)

    # Используем ПРЕКОМПИЛИРОВАННЫЙ паттерн (быстрее в разы)
    # set() удаляет дубликаты сразу
    return list(set(VLESS_PATTERN.findall(decoded_text)))


def get_vless_info(link: str) -> Optional[VlessInfo]:
    try:
        # убираем vless://
        body = link.replace("vless://", "")

        # отделяем название (#name)
        if "#" in body:
            main_part, name_raw = body.split("#", 1)
            name = urllib.parse.unquote(name_raw).strip()
        else:
            main_part = body
            name = "NoName"

        # отделяем параметры (?type=tcp...)
        if "?" in main_part:
            auth_part, query = main_part.split("?", 1)
        else:
            auth_part = main_part
            query = ""

        # отделяем uuid@host:port
        if "@" in auth_part:
            uuid, host_port = auth_part.split("@", 1)
        else:
            return None

        # отделяем host:port
        # rsplit нужен для корректной обработки IPv6 (где двоеточий много)
        if ":" in host_port:
            host, port_str = host_port.rsplit(":", 1)
            port = int(port_str)
        else:
            return None

        # парсим параметры безопасности
        # parse_qs создает словарь списков
        params = urllib.parse.parse_qs(query)

        # Безопасное извлечение параметров (get возвращает список или None)
        security = params.get("security", ["none"])[0]

        # Логика определения SNI: sni -> host -> сам адрес сервера
        sni_list = params.get("sni", [])
        host_param_list = params.get("host", [])

        sni = (
            sni_list[0]
            if sni_list
            else (host_param_list[0] if host_param_list else host)
        )

        return VlessInfo(link, uuid, host, port, security, sni, name)

    except Exception:
        # При ошибке парсинга возвращаем None, чтобы не крашить бота
        return None
