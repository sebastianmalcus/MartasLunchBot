import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

# Läser in konfiguration
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_day_info():
    days_sv = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
    idx = datetime.now().weekday()
    return (idx, days_sv[idx]) if idx < 5 else (None, None)

def scrape_site(url, day_name):
    try:
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        lines = [l.strip() for l in soup.get_text(separator="\n").split('\n') if len(l.strip()) > 8]
        
        menu = []
        found_day = False
        for line in lines:
            if day_name.upper() in line.upper():
                found_day = True
                continue
            if found_day:
                if any(d in line.upper() for d in ["TISDAG", "ONSDAG", "TORSDAG", "FREDAG", "LÖRDAG"]):
                    break
                menu.append(f"• {line}")
        return "\n".join(menu[:4]) if menu else None
    except:
        return None

async def main():
    day_idx, day_name = get_day_info()
    if day_idx is None: return 
    
    # Säkerställ att ID är en siffra (viktigt för Telegram API)
    try:
        target_chat = int(str(CHAT_ID).replace(" ", ""))
        print(f"Försöker skicka till ID: {target_chat}")
    except:
        print(f"Kritisk Error: Ogiltigt Chat ID: {CHAT_ID}")
        return

    bot = Bot(token=TOKEN)
    gabys = scrape_site("https://jacyzhotel.com/restauranger-goteborg/gabys/", day_name) or "🍴 Se menyn på Jacy'z hemsida."
    matsmak = scrape_site("https://matsmak.se/lunch/", day_name) or "⚠️ Menyn ej uppdaterad på sajten."
    
    msg = (
        f"🏙️ *GÅRDA LUNCH - {day_name.upper()}* 🏙️\n\n"
        f"🍸 *Gaby's (Jacy'z)*\n{gabys}\n\n"
        f"🍲 *Matsmak*\n{matsmak}\n\n"
        f"🏘️ *The Village*\n📍 [Se länk](https://www.compass-group.se/restauranger-och-menyer/ovriga-restauranger/village/)\n\n"
        f"🍽️ *Hildas*\n📍 [Se länk](https://hildasrestaurang.se/se/lunch-meny)\n\n"
        "--- \n"
        "Smaklig lunch!"
    )
    
    try:
        await bot.send_message(chat_id=target_chat, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
        print("✅ Success: Postat i gruppen!")
    except Exception as e:
        print(f"❌ ERROR från Telegram: {e}")

if __name__ == "__main__":
    asyncio.run(main())
