import asyncio
import os
import sys

from database.connection import init_models

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tasks.scheduler import update_subscriptions


async def main():
    print("PIPELINE-ONCE: start", flush=True)

    await init_models()
    print("DATABASE: OK", flush=True)

    await update_subscriptions()
    print("PIPELINE-ONCE: done", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("PIPELINE-ONCE: interrupted", flush=True)
