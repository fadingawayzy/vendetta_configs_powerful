import asyncio
import base64
import gc
import os
import random
import time

from aiohttp import web

from database.methods import get_configs_by_country_tiered, get_user_settings

from app.utils.singbox_builder import build_for_profile

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
    except asyncio.CancelledError:
        pass


async def start_background_tasks(app):
    app["cleaner"] = asyncio.create_task(background_cache_cleaner(app))


async def cleanup_background_tasks(app):
    app["cleaner"].cancel()
    await app["cleaner"]


async def handle_sub(request):
    try:
        user_id = int(request.match_info["user_id"])
        now = time.time()
        if user_id in CACHE:
            expire, data = CACHE[user_id]
            if now < expire:
                return web.Response(text=data)
            del CACHE[user_id]

        settings = await get_user_settings(user_id)
        countries, limit = settings if settings else (["US", "DE", "NL"], 20)

        configs = []
        # Грузим с запасом x3
        for code in countries:
            rows = await get_configs_by_country_tiered(code, limit=limit * 3)
            # Ищем правильное поле (link)
            for r in rows:
                val = getattr(r, "link", getattr(r, "full_link", None))
                if val:
                    configs.append(val)

        if not configs:
            return web.Response(text="No configs", status=404)

        random.shuffle(configs)
        configs = configs[:limit]
        text_data = "\n".join(configs)
        b64_data = base64.b64encode(text_data.encode()).decode()
        CACHE[user_id] = (now + TTL, b64_data)
        return web.Response(text=b64_data)
    except:
        return web.Response(status=500)


async def handle_ping(request):
    return web.Response(text="OK")

async def handle_singbox(request):
    try:
        user_id = int(request.match_info["user_id"])
        profile = request.match_info.get("profile", "balanced")

        # Валидация профиля
        valid_profiles = ["balanced", "gaming", "streaming", "paranoid"]
        if profile not in valid_profiles:
            profile = "balanced"

        # Кэш
        cache_key = f"sb_{user_id}_{profile}"
        now = time.time()
        if cache_key in CACHE:
            expire, data = CACHE[cache_key]
            if now < expire:
                return web.Response(
                    text=data,
                    content_type="application/json",
                    headers={"Content-Disposition": f"inline; filename=vendetta_{profile}.json"}
                )
            del CACHE[cache_key]

        # Получаем конфиги юзера
        settings = await get_user_settings(user_id)
        countries, limit = settings if settings else (["US", "DE", "NL"], 20)

        configs = []
        for code in countries:
            rows = await get_configs_by_country_tiered(code, limit=limit * 3)
            for r in rows:
                configs.append({
                    "link": getattr(r, "link", getattr(r, "full_link", "")),
                    "country": getattr(r, "country", ""),
                    "flag": getattr(r, "flag", ""),
                    "ping": getattr(r, "ping", 999),
                    "tier": getattr(r, "tier", 3),
                })

        if not configs:
            return web.Response(text='{"error": "no configs"}', status=404, content_type="application/json")

        # Генерируем Sing-Box JSON
        json_str = build_for_profile(configs, profile)

        CACHE[cache_key] = (now + TTL, json_str)

        return web.Response(
            text=json_str,
            content_type="application/json",
            headers={"Content-Disposition": f"inline; filename=vendetta_{profile}.json"}
        )

    except Exception:
        return web.Response(status=500)

async def start_web_server():
    app = web.Application()
    app.add_routes([
        web.get("/", handle_ping),
        web.get("/sub/{user_id}", handle_sub),
        web.get("/singbox/{user_id}", handle_singbox),
        web.get("/singbox/{user_id}/{profile}", handle_singbox),
    ])
    app.add_routes([web.get("/", handle_ping), web.get("/sub/{user_id}", handle_sub)])
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)

    port_env = os.environ.get("PORT")
    port = int(port_env) if port_env else 8080

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 SERVER LISTENING: 0.0.0.0:{port}")
    return runner
