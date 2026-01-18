import asyncio
import gc

from app.tasks.pipeline.filter import get_filtered_candidates
from app.utils.net_tools import ssl_check, tcp_ping
from config import config
from database.methods import clear_configs_table, save_configs_bulk

TRUSTED_SNI_SET = set(config.TRUSTED_SNI)

TCP_SEM = asyncio.Semaphore(800)
SSL_SEM = asyncio.Semaphore(300)
PREMIUM_PORTS = {443, 8443, 2053, 2083, 2087, 2096}


def calculate_tier(info, port: int) -> int:
    is_trusted = False
    if info.sni:
        for t in TRUSTED_SNI_SET:
            if t in info.sni:
                is_trusted = True
                break

    # Reality + 443 + Trusted SNI = ELITE
    if info.security == "reality" and port == 443 and is_trusted:
        return 1
    # TLS + Premium Ports = GOLD
    if info.security == "tls" and port in PREMIUM_PORTS:
        return 2

    return 3


async def process_candidate(item: dict) -> dict | None:
    info = item["info"]
    host = info.host
    port = info.port

    # Очистка SNI от возможного мусора в начале/конце
    safe_sni = info.sni.strip().strip('"').strip("'") if info.sni else None
    info.sni = safe_sni

    # 1. TCP (Flash Check)
    async with TCP_SEM:
        ping = await tcp_ping(host, port, timeout=1.2)
    if not ping:
        return None

    # 2. SSL (Deep Check)
    if info.security in ["reality", "tls"]:
        async with SSL_SEM:
            # Передаем очищенный SNI
            ssl_ping = await ssl_check(host, port, safe_sni, timeout=2.5)

        if ssl_ping:
            ping = ssl_ping
        else:
            return None

    c_code = item.get("country")
    if not c_code or len(c_code) != 2:
        return None

    tag = f"#{item.get('flag', '')}_{c_code}_{ping}ms"
    full_link = item["original_link"].split("#")[0] + tag

    return {
        "link": full_link,
        "uuid": info.uuid,
        "country": c_code,
        "flag": item["flag"],
        "ping": ping,
        "source": item["source"],
        "tier": calculate_tier(info, port),
        "host": host,
        "port": port,
        "security": info.security,
        "sni": info.sni,
        "protocol": "vless",
        "is_active": True,
    }


async def run_scan():
    print("🔥 PIPELINE: Starting High-Performance Scan...")
    await clear_configs_table()

    # Батчи по 1000, чтобы загрузить UVLOOP
    candidate_stream = get_filtered_candidates(batch_size=1000)
    total = 0
    seen_ips = set()

    async for batch in candidate_stream:
        tasks = [process_candidate(item) for item in batch]
        results = await asyncio.gather(*tasks)

        valid_batch = []
        for res in results:
            if res:
                # Дедупликация IP внутри цикла
                sig = f"{res['host']}:{res['port']}"
                if sig not in seen_ips:
                    seen_ips.add(sig)
                    valid_batch.append(res)

        if valid_batch:
            await save_configs_bulk(valid_batch)
            total += len(valid_batch)
            print(f"   💎 Saved {len(valid_batch)} elite configs.")

        del tasks, results, valid_batch
        gc.collect()

    print(f"🏁 SCAN FINISHED. Total: {total}")
    del seen_ips
    gc.collect()
