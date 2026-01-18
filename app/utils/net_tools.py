import asyncio
import ssl
import time

# Глобальный контекст для экономии ресурсов
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def is_valid_sni(sni: str) -> bool:
    """Проверка валидности SNI перед SSL хендшейком (защита от UnicodeError)."""
    if not sni or not isinstance(sni, str):
        return False
    if len(sni) > 253:
        return False
    # Согласно RFC: каждая метка (между точками) не более 63 символов
    labels = sni.split(".")
    for label in labels:
        if len(label) > 63 or len(label) == 0:
            if len(labels) > 1:  # если это просто IP, пропускаем
                return False
    return True


async def tcp_ping(host: str, port: int, timeout: float = 2.0) -> int | None:
    try:
        t0 = time.perf_counter()
        # Попытка установить TCP соединение
        conn = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        ping = int((time.perf_counter() - t0) * 1000)

        _, writer = conn
        writer.close()
        await writer.wait_closed()
        return ping
    except:
        return None


async def ssl_check(host: str, port: int, sni: str, timeout: float = 3.0) -> int | None:
    # ПРЕДОХРАНИТЕЛЬ: если SNI битый, не пускаем в uvloop/ssl
    target_sni = sni if sni else host
    if not is_valid_sni(target_sni):
        return None

    try:
        t0 = time.perf_counter()
        # Пытаемся сделать SSL Handshake
        conn = await asyncio.wait_for(
            asyncio.open_connection(
                host, port, ssl=SSL_CTX, server_hostname=target_sni
            ),
            timeout=timeout,
        )
        ping = int((time.perf_counter() - t0) * 1000)

        _, writer = conn
        writer.close()
        await writer.wait_closed()
        return ping
    except (asyncio.TimeoutError, Exception):
        # Ловим любые ошибки, включая UnicodeError внутри uvloop
        return None
