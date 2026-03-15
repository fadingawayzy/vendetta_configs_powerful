import asyncio
import base64
import gc
import logging
import os
import random
import time

from aiohttp import web

from database.methods import get_configs_by_country_tiered, get_user_settings
from app.utils.singbox_builder import build_for_profile

logger = logging.getLogger(__name__)

CACHE = {}
TTL = 300


async def background_cache_cleaner(app):
    try:
        while True:
            await asyncio.sleep(60)
            now = time.time()
            keys = [k for k, v in CACHE.items() if v[0] < now]
            if keys:
                for k in keys:
                    del CACHE[k]
                gc.collect()
                logger.info("CACHE_CLEANED removed=%s remaining=%s", len(keys), len(CACHE))
    except asyncio.CancelledError:
        logger.info("CACHE_CLEANER cancelled")


async def start_background_tasks(app):
    app["cleaner"] = asyncio.create_task(background_cache_cleaner(app))


async def cleanup_background_tasks(app):
    cleaner = app.get("cleaner")
    if cleaner:
        cleaner.cancel()
        try:
            await cleaner
        except asyncio.CancelledError:
            pass


async def handle_sub(request):
    try:
        user_id = int(request.match_info["user_id"])
        now = time.time()

        if user_id in CACHE:
            expire, data = CACHE[user_id]
            if now < expire:
                logger.info("SUB_CACHE_HIT user_id=%s", user_id)
                return web.Response(text=data)
            del CACHE[user_id]

        settings = await get_user_settings(user_id)
        countries, limit = settings if settings else (["US", "DE", "NL"], 20)

        configs = []
        for code in countries:
            rows = await get_configs_by_country_tiered(code, limit=limit * 3)
            for row in rows:
                val = getattr(row, "link", getattr(row, "full_link", None))
                if val:
                    configs.append(val)

        if not configs:
            logger.warning("SUB_EMPTY user_id=%s countries=%s limit=%s", user_id, countries, limit)
            return web.Response(text="No configs", status=404)

        random.shuffle(configs)
        configs = configs[:limit]

        text_data = "\n".join(configs)
        b64_data = base64.b64encode(text_data.encode()).decode()

        CACHE[user_id] = (now + TTL, b64_data)

        logger.info(
            "SUB_OK user_id=%s countries=%s selected=%s",
            user_id,
            countries,
            len(configs),
        )
        return web.Response(text=b64_data)

    except ValueError:
        logger.warning("SUB_BAD_USER_ID raw=%s", request.match_info.get("user_id"))
        return web.Response(text="Bad user_id", status=400)
    except Exception:
        logger.exception("SUB_INTERNAL_ERROR user_id=%s", request.match_info.get("user_id"))
        return web.Response(text="Internal server error", status=500)


async def handle_ping(request):
    return web.Response(text="OK")


async def handle_singbox(request):
    try:
        user_id = int(request.match_info["user_id"])
        profile = request.match_info.get("profile", "balanced")

        valid_profiles = ["balanced", "gaming", "streaming", "paranoid"]
        if profile not in valid_profiles:
            profile = "balanced"

        ua = request.headers.get("User-Agent", "").lower()
        is_singbox_client = any(x in ua for x in ["sing-box", "hiddify", "sfi"])

        cache_key = f"sb_{user_id}_{profile}_{'sb' if is_singbox_client else 'b64'}"
        now = time.time()

        if cache_key in CACHE:
            expire, data = CACHE[cache_key]
            if now < expire:
                content_type = "application/json" if is_singbox_client else "text/plain"
                logger.info(
                    "SINGBOX_CACHE_HIT user_id=%s profile=%s mode=%s",
                    user_id,
                    profile,
                    "json" if is_singbox_client else "b64",
                )
                return web.Response(text=data, content_type=content_type)
            del CACHE[cache_key]

        from database.methods import get_top_configs_for_singbox

        rows = await get_top_configs_for_singbox(limit=30)
        configs = []

        for row in rows:
            link = getattr(row, "link", "")
            country = getattr(row, "country", "")

            if country in ("RU", "BY", "CN", "IR"):
                continue

            configs.append(
                {
                    "link": link,
                    "country": country,
                    "flag": getattr(row, "flag", ""),
                    "ping": getattr(row, "ping", 999),
                    "tier": getattr(row, "tier", 3),
                }
            )

        if not configs:
            logger.warning("SINGBOX_EMPTY user_id=%s profile=%s", user_id, profile)
            return web.Response(text="No configs", status=404)

        if is_singbox_client:
            result = build_for_profile(configs, profile)
            content_type = "application/json"
        else:
            links = [c["link"] for c in configs]
            text_data = "\n".join(links)
            result = base64.b64encode(text_data.encode()).decode()
            content_type = "text/plain"

        CACHE[cache_key] = (now + 180, result)

        logger.info(
            "SINGBOX_OK user_id=%s profile=%s configs=%s mode=%s",
            user_id,
            profile,
            len(configs),
            "json" if is_singbox_client else "b64",
        )
        return web.Response(text=result, content_type=content_type)

    except ValueError:
        logger.warning("SINGBOX_BAD_USER_ID raw=%s", request.match_info.get("user_id"))
        return web.Response(text="Bad user_id", status=400)
    except Exception:
        logger.exception(
            "SINGBOX_INTERNAL_ERROR user_id=%s profile=%s",
            request.match_info.get("user_id"),
            request.match_info.get("profile"),
        )
        return web.Response(text="Internal server error", status=500)


async def start_web_server():
    app = web.Application()

    app.add_routes(
        [
            web.get("/", handle_ping),
            web.get("/sub/{user_id}", handle_sub),
            web.get("/singbox/{user_id}", handle_singbox),
            web.get("/singbox/{user_id}/{profile}", handle_singbox),
        ]
    )

    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)

    port_env = os.environ.get("PORT")
    port = int(port_env) if port_env else 8080

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info("SERVER_LISTENING host=0.0.0.0 port=%s", port)
    return runner
