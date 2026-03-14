"""
Vendetta Sing-Box Config Builder
Генерирует конфиги Sing-Box с:
- Сплит-туннелинг (РФ сайты напрямую)
- Авто-балансировка (urltest)
- Блокировка рекламы
- uTLS fingerprint (chrome)
- Kill Switch
"""

import json
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional


# === ПАРСЕР ПОЛНЫХ ПАРАМЕТРОВ ИЗ VLESS ССЫЛКИ ===

@dataclass
class VlessFullInfo:
    """Все параметры VLESS ссылки для Sing-Box."""
    uuid: str = ""
    host: str = ""
    port: int = 443
    security: str = "none"
    sni: str = ""
    transport: str = "tcp"        # tcp, ws, grpc, xhttp, h2
    flow: str = ""                # xtls-rprx-vision
    pbk: str = ""                 # reality public key
    sid: str = ""                 # reality short id
    fp: str = "chrome"            # fingerprint
    path: str = "/"               # websocket/xhttp path
    service_name: str = ""        # grpc service name
    alpn: list = field(default_factory=list)
    tag: str = ""                 # название


def parse_vless_full(link: str) -> Optional[VlessFullInfo]:
    """Парсит VLESS ссылку и извлекает ВСЕ параметры."""
    try:
        body = link.replace("vless://", "")

        # Отделяем tag (#name)
        tag = ""
        if "#" in body:
            body, tag_raw = body.split("#", 1)
            tag = urllib.parse.unquote(tag_raw).strip()

        # Отделяем параметры
        query = ""
        if "?" in body:
            body, query = body.split("?", 1)

        # UUID и host:port
        if "@" not in body:
            return None

        uuid, host_port = body.split("@", 1)

        if ":" not in host_port:
            return None

        host, port_str = host_port.rsplit(":", 1)
        # Убираем скобки IPv6
        host = host.strip("[]")

        params = urllib.parse.parse_qs(query)

        def get_param(key, default=""):
            val = params.get(key, [default])
            return val[0] if val else default

        info = VlessFullInfo(
            uuid=uuid,
            host=host,
            port=int(port_str),
            security=get_param("security", "none"),
            sni=get_param("sni", ""),
            transport=get_param("type", "tcp"),
            flow=get_param("flow", ""),
            pbk=get_param("pbk", ""),
            sid=get_param("sid", ""),
            fp=get_param("fp", "chrome"),
            path=get_param("path", "/"),
            service_name=get_param("serviceName", ""),
            tag=tag,
        )

        # ALPN
        alpn_raw = get_param("alpn", "")
        if alpn_raw:
            info.alpn = alpn_raw.split(",")

        # Если SNI пустой — берём host-параметр
        if not info.sni:
            info.sni = get_param("host", info.host)

        return info

    except Exception:
        return None


# === КОНСТАНТЫ ===

RU_DIRECT_DOMAINS = [
    ".sberbank.ru", ".tinkoff.ru", ".vtb.ru", ".alfabank.ru",
    ".gosuslugi.ru", ".nalog.gov.ru", ".mos.ru", ".kremlin.ru",
    ".yandex.ru", ".yandex.net", ".ya.ru", ".yandex.com",
    ".mail.ru", ".vk.com", ".ok.ru", ".dzen.ru",
    ".wildberries.ru", ".ozon.ru", ".avito.ru",
    ".megafon.ru", ".mts.ru", ".beeline.ru", ".tele2.ru",
    ".rt.ru", ".rostelecom.ru", ".domru.ru",
    ".pochta.ru", ".rzd.ru", ".aeroflot.ru",
    ".kinopoisk.ru", ".ivi.ru",
]

PROFILES = {
    "balanced": {
        "name": "🛡 Баланс",
        "description": "YouTube + Discord + обход блокировок",
        "max_ping": 300,      # было 200, расширяем
        "min_tier": 3,
        "limit": 20,          # было 10, больше кандидатов
        "countries": None,
    },
    "gaming": {
        "name": "🎮 Игровой",
        "description": "Минимальный пинг для игр и Discord",
        "max_ping": 80,
        "min_tier": 2,
        "limit": 15,          # было 5
        "countries": ["DE", "FI", "SE", "PL", "NL", "LV", "LT", "EE"],
    },
    "streaming": {
        "name": "🎬 Стриминг",
        "description": "YouTube, Netflix, Twitch — максимальная скорость",
        "max_ping": 200,
        "min_tier": 2,
        "limit": 20,          # было 10
        "countries": ["DE", "NL", "US", "GB", "SE", "FI"],
    },
    "paranoid": {
        "name": "🔒 Паранойя",
        "description": "Максимальная приватность",
        "max_ping": 400,
        "min_tier": 2,
        "limit": 15,          # было 5
        "countries": ["CH", "IS", "NO", "RO", "MD", "LU"],
    },
}


# === BUILDER ===

class SingBoxBuilder:
    """Конструктор Sing-Box конфигов."""

    def __init__(self):
        self.outbounds = []
        self.route_rules = []
        self.dns_rules = []
        self._split_routing = False
        self._ads_blocked = False

    def add_nodes_from_db(self, configs: list) -> "SingBoxBuilder":
        """
        Принимает список объектов Config из базы.
        Парсит link каждого и создаёт outbound.
        """
        for cfg in configs:
            link = cfg.link if hasattr(cfg, 'link') else cfg.get('link', '')
            country = cfg.country if hasattr(cfg, 'country') else cfg.get('country', '')
            flag = cfg.flag if hasattr(cfg, 'flag') else cfg.get('flag', '')
            ping = cfg.ping if hasattr(cfg, 'ping') else cfg.get('ping', 0)

            info = parse_vless_full(link)
            if not info:
                continue

            outbound = self._build_outbound(info, country, flag, ping)
            if outbound:
                self.outbounds.append(outbound)

        return self

    def add_auto_select(self, interval: str = "30s", tolerance: int = 100) -> "SingBoxBuilder":
        """Агрессивный авто-выбор — проверка каждые 30 секунд."""
        proxy_tags = [
            o["tag"] for o in self.outbounds
            if o["type"] in ("vless", "hysteria2", "trojan")
        ]

        if not proxy_tags:
            return self

        # Основная группа — urltest
        self.outbounds.append({
            "type": "urltest",
            "tag": "⚡ Auto",
            "outbounds": proxy_tags,
            "url": "https://cp.cloudflare.com/generate_204",
            "interval": interval,       # Каждые 30 секунд
            "tolerance": tolerance,     # 100ms допуск
            "idle_timeout": "30m",
        })

        return self

    def add_split_routing(self) -> "SingBoxBuilder":
        """РФ сайты напрямую, остальное через VPN."""
        self._split_routing = True

        self.route_rules.append({
            "domain_suffix": RU_DIRECT_DOMAINS,
            "outbound": "🇷🇺 Direct",
        })

        self.route_rules.append({
            "rule_set": ["geoip-ru", "geosite-category-ru"],
            "outbound": "🇷🇺 Direct",
        })

        self.dns_rules.append({
            "domain_suffix": [".ru", ".рф", ".su"],
            "server": "local",
        })

        return self

    def add_ads_block(self) -> "SingBoxBuilder":
        """Блокировка рекламы."""
        self._ads_blocked = True

        self.route_rules.append({
            "rule_set": "geosite-category-ads-all",
            "outbound": "🚫 Block",
        })
        return self

    def build(self) -> dict:
        """Собирает финальный конфиг."""
        system_outbounds = [
            {"type": "direct", "tag": "🇷🇺 Direct"},
            {"type": "block", "tag": "🚫 Block"},
            {"type": "dns", "tag": "dns-out"},
        ]

        auto_tag = "⚡ Auto"
        has_auto = any(o.get("tag") == auto_tag for o in self.outbounds)

        if has_auto:
            default_out = auto_tag
        elif self.outbounds:
            default_out = self.outbounds[0]["tag"]
        else:
            default_out = "🇷🇺 Direct"

        # Rule sets
        rule_sets = []
        if self._split_routing:
            rule_sets.extend([
                {
                    "tag": "geoip-ru",
                    "type": "remote",
                    "url": "https://raw.githubusercontent.com/SagerNet/sing-geoip/rule-set/geoip-ru.srs",
                    "format": "binary",
                },
                {
                    "tag": "geosite-category-ru",
                    "type": "remote",
                    "url": "https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-category-ru.srs",
                    "format": "binary",
                },
            ])
        if self._ads_blocked:
            rule_sets.append({
                "tag": "geosite-category-ads-all",
                "type": "remote",
                "url": "https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-category-ads-all.srs",
                "format": "binary",
            })

        return {
            "log": {"level": "warn", "timestamp": True},
            "dns": {
                "independent_cache": True,
                "servers": [
                    {
                        "tag": "google",
                        "address": "tls://8.8.8.8",
                        "detour": default_out,
                    },
                    {
                        "tag": "local",
                        "address": "77.88.8.8",
                        "detour": "🇷🇺 Direct",
                    },
                ],
                "rules": self.dns_rules + [
                    {"outbound": "any", "server": "google"}
                ],
            },
            "inbounds": [
                {
                    "type": "tun",
                    "tag": "tun-in",
                    "inet4_address": "172.19.0.1/30",
                    "inet6_address": "fdfe:dcba:9876::1/126",
                    "auto_route": True,
                    "strict_route": True,
                    "sniff": True,
                    "sniff_override_destination": True,
                }
            ],
            "outbounds": self.outbounds + system_outbounds,
            "route": {
                "rules": [
                    {"protocol": "dns", "outbound": "dns-out"},
                ] + self.route_rules + [
                    {"outbound": default_out},
                ],
                "rule_set": rule_sets,
                "auto_detect_interface": True,
            },
        }

    def build_json(self, indent: int = 2) -> str:
        """Возвращает готовый JSON-строкой."""
        return json.dumps(self.build(), indent=indent, ensure_ascii=False)

    # === ПРИВАТНЫЕ МЕТОДЫ ===

    def _build_outbound(self, info: VlessFullInfo,
                        country: str, flag: str, ping: int) -> Optional[dict]:
        """Конвертирует VlessFullInfo в Sing-Box outbound."""

        tag = f"{flag} {country} {ping}ms"

        out = {
            "type": "vless",
            "tag": tag,
            "server": info.host,
            "server_port": info.port,
            "uuid": info.uuid,
        }

        # Flow (для XTLS)
        if info.flow:
            out["flow"] = info.flow

        # TLS
        tls = {
            "enabled": True,
            "server_name": info.sni,
            "utls": {
                "enabled": True,
                "fingerprint": info.fp or "chrome",
            },
        }

        # ALPN
        if info.alpn:
            tls["alpn"] = info.alpn

        # Reality
        if info.security == "reality":
            tls["reality"] = {
                "enabled": True,
                "public_key": info.pbk,
                "short_id": info.sid,
            }

        out["tls"] = tls

        # Transport
        if info.transport == "ws":
            out["transport"] = {
                "type": "ws",
                "path": info.path,
                "headers": {"Host": info.sni},
            }
        elif info.transport == "grpc":
            out["transport"] = {
                "type": "grpc",
                "service_name": info.service_name or info.path.strip("/"),
            }
        elif info.transport == "xhttp":
            out["transport"] = {
                "type": "xhttp",
                "host": info.sni,
                "path": info.path,
            }
        elif info.transport == "h2":
            out["transport"] = {
                "type": "http",
                "host": [info.sni],
                "path": info.path,
            }
        # tcp — без transport блока

        return out


# === ФАБРИЧНЫЕ ФУНКЦИИ ===

def build_for_profile(configs: list, profile_name: str = "balanced") -> str:
    """
    Основная функция: принимает список конфигов из БД,
    возвращает готовый JSON для Sing-Box.

    Использование:
        configs = await get_configs_for_singbox(profile)
        json_str = build_for_profile(configs, "gaming")
    """
    profile = PROFILES.get(profile_name, PROFILES["balanced"])

    # Фильтруем по профилю
    filtered = []
    for cfg in configs:
        ping = cfg.ping if hasattr(cfg, 'ping') else cfg.get('ping', 999)
        tier = cfg.tier if hasattr(cfg, 'tier') else cfg.get('tier', 3)
        country = cfg.country if hasattr(cfg, 'country') else cfg.get('country', '')

        if ping > profile["max_ping"]:
            continue
        if tier > profile["min_tier"]:
            continue
        if profile["countries"] and country not in profile["countries"]:
            continue

        filtered.append(cfg)

    # Берём лучших по лимиту
    filtered = filtered[:profile["limit"]]

    if not filtered:
        # Если под профиль ничего не подошло — берём лучшие из всех
        filtered = sorted(configs, key=lambda c: c.ping if hasattr(c, 'ping') else c.get('ping', 999))[:5]

    builder = SingBoxBuilder()
    builder.add_nodes_from_db(filtered)
    builder.add_auto_select()
    builder.add_split_routing()
    builder.add_ads_block()

    return builder.build_json()


def get_available_profiles() -> dict:
    """Возвращает словарь профилей для отображения в боте."""
    return PROFILES