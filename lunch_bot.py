import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

async def main():
    if not TOKEN or not CHAT_ID:
        print("FEL: Saknar Token eller Chat ID i GitHub Secrets!")
        return

    bot = Bot(token=TOKEN)
    day_name = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"][datetime.now().weekday()]
    
    # Rensa ID-numret ordentligt
    clean_id = int(str(CHAT_ID).strip())
    print(f"Försöker skicka till ID: {clean_id}")

    msg = f"🚀 **TESTKÖRNING - {day_name.upper()}**\n\nOm du ser detta fungerar boten!"

    try:
        # Vi skickar ett superenkelt meddelande först för att testa anslutningen
        await bot.send_message(chat_id=clean_id, text=msg, parse_mode='Markdown')
        print("✅ SUCCESS: Meddelandet gick fram!")
    except Exception as e:
        print(f"❌ ERROR från Telegram: {e}")

if __name__ == "__main__":
    asyncio.run(main())
