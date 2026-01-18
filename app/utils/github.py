import os

import aiohttp
from dotenv import load_dotenv

from config import GITHUB_TOKEN

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


async def update_gist(gist_id: str, filename: str, content: str) -> bool:
    url = f"https://api.github.com/gists/{gist_id}"

    payload = {"files": {filename: {"content": content}}}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, json=payload, headers=HEADERS) as resp:
                if resp.status == 200:
                    return True
                else:
                    print(f"Gist Error {resp.status}: {await resp.text()}")
                    return False
    except Exception as e:
        print(f"Gist Network Error: {e}")
        return False
