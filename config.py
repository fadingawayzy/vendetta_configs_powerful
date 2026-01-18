import os
import sys

from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    def __init__(self):
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "postgres")
        self.name = os.getenv("DB_NAME", "postgres")
        self.host = os.getenv("DB_HOST", "db")
        self.port = os.getenv("DB_PORT", "5432")

    @property
    def url(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def url_alembic(self):
        return self.url


class Config:
    __slots__ = ("bot_token", "admin_password", "github_token", "APP_BASE_URL")

    def __init__(self):
        token = os.getenv("BOT_TOKEN")
        if not token:
            print("❌ CRITICAL: BOT_TOKEN is missing!")
            sys.exit(1)
        self.bot_token = str(token)

        self.admin_password = os.getenv("ADMIN_PASSWORD")
        self.github_token = os.getenv("GITHUB_TOKEN")

        # Настройка ссылки для кастомного сета
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8080")
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.APP_BASE_URL = base_url

    WHITELIST_SOURCES = {
        "Mobile": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
        "SNI": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-SNI-RU-all.txt",
    }
    database = DatabaseConfig()

    # Оптимизированные списки
    TRUSTED_SNI = [
        "google",
        "googlevideo",
        "microsoft",
        "azure",
        "amazon",
        "aws",
        "cloudflare",
        "yahoo",
        "apple",
        "github",
        "discord",
        "telegram",
        "whatsapp",
        "speedtest",
    ]

    # Источники оставлены полными, фильтр справится
    SUBSCRIPTION_SOURCES = {
        "LINK1": "https://raw.githubusercontent.com/sakha1370/OpenRay/refs/heads/main/output/all_valid_proxies.txt",
        "LINK2": "https://raw.githubusercontent.com/yitong2333/proxy-minging/refs/heads/main/v2ray.txt",
        "LINK3": "https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt",
        "LINK4": "https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/refs/heads/main/config.txt",
        "LINK5": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt",
        "LINK6": "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/trojan.txt",
        "LINK7": "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt",
        "LINK8": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/BLACK_VLESS_RUS.txt",
        "LINK9": "https://raw.githubusercontent.com/hamedcode/port-based-v2ray-configs/main/sub/vless.txt",
        "LINK10": "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/vpn-files/all_posts.txt",
        "LINK11": "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity",
        "LINK12": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt",
        "LINK13": "https://github.com/AvenCores/goida-vpn-configs/raw/refs/heads/main/githubmirror/5.txt",
        "LINK 14": "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/22.txt",
        "LINK 15": "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/23.txt",
        "LINK 16": "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/1.txt",
        "LINK 17": "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/24.txt",
        "LINK 18": "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/25.txt",
        "LINK 19": "https://github.com/sakha1370/OpenRay/blob/main/output/all_valid_proxies.txt",
        "LINK 20": "https://github.com/sakha1370/OpenRay/blob/main/output/country/DE.txt",
        "LINK 21": "https://github.com/sakha1370/OpenRay/blob/main/output/country/NL.txt",
        "LINK 22": "https://github.com/sakha1370/OpenRay/blob/main/output/country/BG.txt",
        "LINK 23": "https://github.com/sakha1370/OpenRay/blob/main/output/country/CA.txt",
        "LINK 24": "https://github.com/sakha1370/OpenRay/blob/main/output/country/GB.txt",
        "LINK 25": "https://github.com/sakha1370/OpenRay/blob/main/output/country/PL.txt",
        "LINK 26": "https://github.com/sakha1370/OpenRay/blob/main/output/country/US.txt",
    }

    GIST_SLOTS = {
        "SLOT_1": "https://gist.githubusercontent.com/fadingawayzy/b6f025c55a79c9ac594df7cf85923fd8/raw/Sub_Slot_1.txt",
        "SLOT_2": "https://gist.githubusercontent.com/fadingawayzy/d704cba52a10258b608e7b816c154a29/raw/Sub_Slot_2.txt",
        "SLOT_3": "https://gist.githubusercontent.com/fadingawayzy/dd141d549c329dc63c77148c9fb75904/raw/Sub_Slot_3.txt",
        "SLOT_4": "https://gist.githubusercontent.com/fadingawayzy/45b5cc88febea751eb70f99e49fd335e/raw/Sub_Slot_4.txt",
        "SLOT_5": "https://gist.githubusercontent.com/fadingawayzy/bd974eee8868df466257a2d16c74a6d6/raw/Sub_Slot_5.txt",
        "SLOT_6": "https://gist.githubusercontent.com/fadingawayzy/0032c9ed68c892b5c933d9863ef8fad3/raw/Sub_Slot_6.txt",  # SNI
        "SLOT_7": "https://gist.githubusercontent.com/fadingawayzy/e437b60a0e9c33747aa3fff6d3c2ca9c/raw/Sub_Slot_7.txt",  # CIDR
    }


"""
ДЛЯ ЛОКАЛЬНЫХ ТЕСТОВ
    GIST_SLOTS = {
        "SLOT_1": "https://gist.githubusercontent.com/hexagonoid/e0e4d54cfbbb4db8c42256424927d6cb/raw/sub.txt",
        "SLOT_2": "https://gist.githubusercontent.com/hexagonoid/a14c12bc20cf59b423817f5c4cfb8108/raw/sub.txt",
        "SLOT_3": "https://gist.githubusercontent.com/hexagonoid/86bb8a69adb4ef9e623d24e380cdcf17/raw/sub.txt",
        "SLOT_4": "https://gist.githubusercontent.com/hexagonoid/14c33c6ea605138786bc4dbdbb844a41/raw/sub.txt",
        "SLOT_5": "https://gist.githubusercontent.com/hexagonoid/b723d9782621f1da6255efedbd38f5c8/raw/sub.txt",
        "SLOT_6": "https://gist.githubusercontent.com/hexagonoid/dca6e953c469ff79f24647e531db8c79/raw/sub.txt",
        "SLOT_7": "https://gist.githubusercontent.com/hexagonoid/005534065451b4f74e48655de6df51cd/raw/sub.txt",
    }
"""


config = Config()
# Экспорт переменных
BOT_TOKEN = config.bot_token
ADMIN_PASSWORD = config.admin_password
SUBSCRIPTION_SOURCES = config.SUBSCRIPTION_SOURCES
GIST_SLOTS = config.GIST_SLOTS
TRUSTED_SNI = config.TRUSTED_SNI
GITHUB_TOKEN = config.github_token
