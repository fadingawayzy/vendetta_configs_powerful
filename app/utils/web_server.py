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

        valid_profiles = ["balanced", "gaming", "streaming", "paranoid"]
        if profile not in valid_profiles:
            profile = "balanced"

        # Определяем клиент по User-Agent
        ua = request.headers.get("User-Agent", "").lower()
        
        # Sing-Box JSON для совместимых клиентов
        is_singbox_client = any(x in ua for x in [
            "sing-box", "hiddify", "sfi",
        ])

        cache_key = f"sb_{user_id}_{profile}_{'sb' if is_singbox_client else 'b64'}"
        now = time.time()
        if cache_key in CACHE:
            expire, data = CACHE[cache_key]
            if now < expire:
                ct = "application/json" if is_singbox_client else "text/plain"
                return web.Response(text=data, content_type=ct)
            del CACHE[cache_key]

        from database.methods import get_top_configs_for_singbox

        rows = await get_top_configs_for_singbox(limit=30)

        configs = []
        for r in rows:
            link = getattr(r, "link", "")
            country = getattr(r, "country", "")

            if country in ("RU", "BY", "CN", "IR"):
                continue

            configs.append({
                "link": link,
                "country": country,
                "flag": getattr(r, "flag", ""),
                "ping": getattr(r, "ping", 999),
                "tier": getattr(r, "tier", 3),
            })

        if not configs:
            return web.Response(text="No configs", status=404)

        if is_singbox_client:
            # Sing-Box JSON
            result = build_for_profile(configs, profile)
            content_type = "application/json"
        else:
            # Base64 для V2RayNG, NekoBox и остальных
            links = [c["link"] for c in configs]
            text_data = "\n".join(links)
            result = base64.b64encode(text_data.encode()).decode()
            content_type = "text/plain"

        CACHE[cache_key] = (now + 180, result)

        return web.Response(text=result, content_type=content_type)

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
