import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

# Hämtar från GitHub Secrets
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
        
        # Hämta all text och rensa bort tomma rader
        lines = [l.strip() for l in soup.get_text(separator="\n").split('\n') if len(l.strip()) > 8]
        
        menu = []
        found_day = False
        for line in lines:
            if day_name.upper() in line.upper():
                found_day = True
                continue
            if found_day:
                # Stoppa om vi når nästa dag
                next_days = ["TISDAG", "ONSDAG", "TORSDAG", "FREDAG", "LÖRDAG"]
                if any(d in line.upper() for d in next_days if d != day_name.upper()):
                    break
                menu.append(f"• {line}")
        
        return "\n".join(menu[:4]) if menu else None
    except:
        return None

async def main():
    day_idx, day_name = get_day_info()
    if day_idx is None: 
        print("Det är helg!")
        return 
    
    bot = Bot(token=TOKEN)
    
    # TVINGA ID-NUMRET TILL INTEGER (Fixar "Chat not found" om GitHub skickar sträng)
    try:
        # Tar bort eventuella mellanslag och gör till siffra
        target_id = int(str(CHAT_ID).strip())
        print(f"DEBUG: Försöker skicka till Chat ID: {target_id}")
    except Exception as e:
        print(f"Kritisk Error: CHAT_ID '{CHAT_ID}' är inte ett giltigt nummer: {e}")
        return

    # Kör scraping
    gabys = scrape_site("https://jacyzhotel.com/restauranger-goteborg/gabys/", day_name) or "🍴 Se menyn på Jacy'z hemsida."
    matsmak = scrape_site("https://matsmak.se/lunch/", day_name) or "⚠️ Menyn ej uppdaterad på sajten."
    
    msg = (
        f"🏙️ *GÅRDA LUNCH - {day_name.upper()}* 🏙️\n\n"
        f"🍸 *Gaby's (Jacy'z)*\n{gabys}\n\n"
        f"🍲 *Matsmak*\n{matsmak}\n\n"
        f"🏘️ *The Village*\n📍 [Se menyn här](https://www.compass-group.se/restauranger-och-menyer/ovriga-restauranger/village/)\n\n"
        f"🍽️ *Hildas*\n📍 [Se menyn här](https://hildasrestaurang.se/se/lunch-meny)\n\n"
        "--- \n"
        "Smaklig lunch!"
    )
    
    try:
        await bot.send_message(chat_id=target_id, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
        print("Success: Meddelande skickat till gruppen!")
    except Exception as e:
        print(f"Misslyckades att skicka med Markdown: {e}")
        # Sista försöket utan formatering
