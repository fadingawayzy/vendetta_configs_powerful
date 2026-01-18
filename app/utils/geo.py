import os
import socket

import IP2Location

# Путь к базе
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "IP2LOCATION-LITE-DB1.BIN")

# Глобальная переменная
_reader = None


def init_geo():
    global _reader
    if os.path.exists(DB_PATH):
        try:
            _reader = IP2Location.IP2Location(DB_PATH)
            print("🌍 IP2Location: База загружена (Легкая версия)")
        except Exception as e:
            print(f"⚠️ ip2location error: {e}")
    else:
        print(f"⚠️ ip2location: Файл не найден {DB_PATH}")


def get_country(host: str) -> tuple[str, str]:
    # Возвращает (код_страны, флаг)

    if not _reader:
        return "UNK", "🏳️"

    try:
        # Резолвим домен в ip
        ip = socket.gethostbyname(host)

        # Ищем запись в базе
        rec = _reader.get_all(ip)

        # Из возвращаемого объекта берем код страны (таблица из твоей доки)
        code = rec.country_short

        if not code or code == "-":
            return "UNK", "🏳️"

        # Превращение кода в флаг
        flag = chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)
        return code, flag

    except Exception:
        return "UNK", "🏳️"


init_geo()
