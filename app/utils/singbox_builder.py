"""
Vendetta Sing-Box Config Builder v2 (Ironclad)
"""

import json
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VlessFullInfo:
    uuid: str = ""
    host: str = ""
    port: int = 443
    security: str = "none"
    sni: str = ""
    transport: str = "tcp"
    flow: str = ""
    pbk: str = ""
    sid: str = ""
    fp: str = "chrome"
    path: str = "/"
    service_name: str = ""
    alpn: list = field(default_factory=list)
    tag: str = ""


def parse_vless_full(link: str) -> Optional[VlessFullInfo]:
    try:
        body = link.replace("vless://", "")

        tag = ""
        if "#" in body:
            body, tag_raw = body.split("#", 1)
            tag = urllib.parse.unquote(tag_raw).strip()

        query = ""
        if "?" in body:
            body, query = body.split("?", 1)

        if "@" not in body:
            return None

        uuid, host_port = body.split("@", 1)

        if ":" not in host_port:
            return None

        host, port_str = host_port.rsplit(":", 1)
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

        alpn_raw = get_param("alpn", "")
        if alpn_raw:
            info.alpn = alpn_raw.split(",")

        if not info.sni:
            info.sni = get_param("host", info.host)

        return info

    except Exception:
        return None


PROFILES = {
    "balanced": {
        "name": "🛡 Баланс",
        "description": "YouTube + Discord + обход блокировок",
        "max_ping": 300,
        "min_tier": 3,
        "limit": 20,
        "countries": None,
    },
    "gaming": {
        "name": "🎮 Игровой",
        "description": "Минимальный пинг для игр и Discord",
        "max_ping": 80,
        "min_tier": 2,
        "limit": 15,
        "countries": ["DE", "FI", "SE", "PL", "NL", "LV", "LT", "EE"],
    },
    "streaming": {
        "name": "🎬 Стриминг",
        "description": "YouTube, Netflix, Twitch",
        "max_ping": 200,
        "min_tier": 2,
        "limit": 20,
        "countries": ["DE", "NL", "US", "GB", "SE", "FI"],
    },
    "paranoid": {
        "name": "🔒 Паранойя",
        "description": "Максимальная приватность",
        "max_ping": 400,
        "min_tier": 2,
        "limit": 15,
        "countries": ["CH", "IS", "NO", "RO", "MD", "LU"],
    },
}


class SingBoxBuilder:

    def __init__(self):
        self.outbounds = []
        self._used_tags = set()
        self._node_tags = []

    def _make_unique_tag(self, country: str, flag: str, ping: int, host: str) -> str:
        """Гарантированно уникальный тег."""
        base = f"{flag}{country}_{ping}ms"
        tag = base
        counter = 1
        while tag in self._used_tags:
            counter += 1
            tag = f"{base}_{counter}"
        self._used_tags.add(tag)
        return tag

    def add_nodes_from_db(self, configs: list) -> "SingBoxBuilder":
        for cfg in configs:
            link = cfg.get("link", "") if isinstance(cfg, dict) else getattr(cfg, "link", "")
            country = cfg.get("country", "") if isinstance(cfg, dict) else getattr(cfg, "country", "")
            flag = cfg.get("flag", "") if isinstance(cfg, dict) else getattr(cfg, "flag", "")
            ping = cfg.get("ping", 0) if isinstance(cfg, dict) else getattr(cfg, "ping", 0)

            info = parse_vless_full(link)
            if not info:
                continue

            tag = self._make_unique_tag(country, flag, ping, info.host)
            outbound = self._build_outbound(info, tag)
            if outbound:
                self.outbounds.append(outbound)
                self._node_tags.append(tag)

        return self

    def _build_outbound(self, info: VlessFullInfo, tag: str) -> Optional[dict]:
        out = {
            "type": "vless",
            "tag": tag,
            "server": info.host,
            "server_port": info.port,
            "uuid": info.uuid,
        }

        if info.flow:
            out["flow"] = info.flow

        tls = {
            "enabled": True,
            "server_name": info.sni if info.sni else info.host,
            "insecure": False,
        }

        if info.fp:
            tls["utls"] = {
                "enabled": True,
                "fingerprint": info.fp,
            }

        if info.alpn:
            tls["alpn"] = info.alpn

        if info.security == "reality":
            tls["reality"] = {
                "enabled": True,
                "public_key": info.pbk,
                "short_id": info.sid,
            }

        out["tls"] = tls

        if info.transport == "ws":
            out["transport"] = {
                "type": "ws",
                "path": info.path,
                "headers": {"Host": info.sni if info.sni else info.host},
            }
        elif info.transport == "grpc":
            sn = info.service_name if info.service_name else info.path.strip("/")
            if sn:
                out["transport"] = {
                    "type": "grpc",
                    "service_name": sn,
                }
        elif info.transport == "h2":
            out["transport"] = {
                "type": "http",
                "host": [info.sni if info.sni else info.host],
                "path": info.path,
            }

        return out

    def build(self) -> dict:
        # Urltest
        if self._node_tags:
            self.outbounds.append({
                "type": "urltest",
                "tag": "auto",
                "outbounds": list(self._node_tags),
                "url": "https://cp.cloudflare.com/generate_204",
                "interval": "30s",
                "tolerance": 100,
            })

        # System outbounds
        self.outbounds.extend([
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            {"type": "dns", "tag": "dns-out"},
        ])

        default_out = "auto" if self._node_tags else "direct"

        config = {
            "log": {
                "level": "warn",
                "timestamp": True,
            },
            "dns": {
                "independent_cache": True,
                "servers": [
                    {
                        "tag": "dns-google",
                        "address": "tls://8.8.8.8",
                        "detour": default_out,
                    },
                    {
                        "tag": "dns-local",
                        "address": "77.88.8.8",
                        "detour": "direct",
                    },
                    {
                        "tag": "dns-block",
                        "address": "rcode://success",
                    },
                ],
                "rules": [
                    {
                        "domain_suffix": [".ru", ".su", ".xn--p1ai"],
                        "server": "dns-local",
                    },
                    {
                        "rule_set": "geosite-category-ads-all",
                        "server": "dns-block",
                        "disable_cache": True,
                    },
                    {
                        "outbound": "any",
                        "server": "dns-google",
                    },
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
            "outbounds": self.outbounds,
            "route": {
                "rules": [
                    {
                        "protocol": "dns",
                        "outbound": "dns-out",
                    },
                    {
                        "domain_suffix": [
                            ".ru", ".su", ".xn--p1ai",
                            ".sberbank.ru", ".tinkoff.ru", ".vtb.ru",
                            ".alfabank.ru", ".gosuslugi.ru", ".nalog.gov.ru",
                            ".mos.ru", ".yandex.ru", ".yandex.net",
                            ".ya.ru", ".yandex.com", ".mail.ru",
                            ".vk.com", ".ok.ru", ".dzen.ru",
                            ".wildberries.ru", ".ozon.ru", ".avito.ru",
                            ".megafon.ru", ".mts.ru", ".beeline.ru",
                            ".tele2.ru", ".rt.ru", ".rostelecom.ru",
                            ".pochta.ru", ".rzd.ru", ".aeroflot.ru",
                            ".kinopoisk.ru", ".ivi.ru",
                        ],
                        "outbound": "direct",
                    },
                    {
                        "rule_set": "geoip-ru",
                        "outbound": "direct",
                    },
                    {
                        "rule_set": "geosite-category-ads-all",
                        "outbound": "block",
                    },
                    {
                        "outbound": default_out,
                    },
                ],
                "rule_set": [
                    {
                        "tag": "geoip-ru",
                        "type": "remote",
                        "url": "https://raw.githubusercontent.com/SagerNet/sing-geoip/rule-set/geoip-ru.srs",
                        "format": "binary",
                    },
                    {
                        "tag": "geosite-category-ads-all",
                        "type": "remote",
                        "url": "https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-category-ads-all.srs",
                        "format": "binary",
                    },
                ],
                "auto_detect_interface": True,
            },
        }

        return config

    def build_json(self, indent: int = 2) -> str:
        return json.dumps(self.build(), indent=indent, ensure_ascii=False)


def build_for_profile(configs: list, profile_name: str = "balanced") -> str:
    profile = PROFILES.get(profile_name, PROFILES["balanced"])

    filtered = []
    for cfg in configs:
        ping = cfg.get("ping", 999) if isinstance(cfg, dict) else getattr(cfg, "ping", 999)
        tier = cfg.get("tier", 3) if isinstance(cfg, dict) else getattr(cfg, "tier", 3)
        country = cfg.get("country", "") if isinstance(cfg, dict) else getattr(cfg, "country", "")

        if ping > profile["max_ping"]:
            continue
        if tier > profile["min_tier"]:
            continue
        if profile["countries"] and country not in profile["countries"]:
            continue

        filtered.append(cfg)

    filtered = filtered[:profile["limit"]]

    if not filtered:
        all_sorted = sorted(
            configs,
            key=lambda c: c.get("ping", 999) if isinstance(c, dict) else getattr(c, "ping", 999)
        )
        filtered = all_sorted[:5]

    builder = SingBoxBuilder()
    builder.add_nodes_from_db(filtered)

    return builder.build_json()


def get_available_profiles() -> dict:
    return PROFILES