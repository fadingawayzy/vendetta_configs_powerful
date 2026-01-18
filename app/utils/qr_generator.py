import asyncio
import gc
from io import BytesIO

import qrcode


def _draw_qr(text):
    qr = None
    img = None
    bio = BytesIO()

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(bio, "PNG")
        bio.seek(0)

        return bio
    except Exception as e:
        print(f"QR Error: {e}")
        return BytesIO()
    finally:
        # Жесткая очистка локальных переменных
        if img:
            del img
        if qr:
            del qr
        # Вызов GC внутри потока генерации (важно!)
        gc.collect()


async def generate_single_qr(text: str) -> BytesIO:
    # Запускаем в отдельном потоке, чтобы не блокировать Event Loop
    return await asyncio.to_thread(_draw_qr, text)
