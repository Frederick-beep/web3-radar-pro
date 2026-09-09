import aiohttp
from app.core.config import settings
async def send_telegram(text:str):
    if not settings.telegram_bot_token or not settings.telegram_chat_id:return
    url=f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(url,json={"chat_id":settings.telegram_chat_id,"text":text})
    except Exception: pass
