import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_day_info():
    days_sv = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
    idx = datetime.now().weekday()
    return (idx, days_sv[idx]) if idx < 5 else (None, None)

def scrape_gabys():
    try:
        url = "https://jacyzhotel.com/restauranger-goteborg/gabys/"
        # Jacy'z blockerar ofta enkla scripts, vi låtsas vara en webbläsare
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        _, day_name = get_day_info()
        
        # Vi letar i ALL text på sidan och delar upp den i rader
        lines = [line.strip() for line in soup.get_text(separator="\n").split("\n") if len(line.strip()) > 5]
        
        menu = []
        found_day = False
        for line in lines:
            # Letar efter t.ex. "TORSDAG" eller "Torsdag"
            if day_name.upper() in line.upper():
                found_day = True
                continue
            if found_day:
                # Sluta om vi når nästa veckodag
                if any(d in line.upper() for d in ["TISDAG", "ONSDAG", "TORSDAG", "FREDAG", "LÖRDAG"]):
                    break
                # Lägg till raden om den ser ut som en maträtt (inte bara ett pris eller kort ord)
                if len(line) > 15:
                    menu.append(f"• {line}")
        
        return "\n".join(menu[:4]) if menu else "🍴 Buffé serveras (se hemsidan för detaljer)."
    except Exception as e:
        return f"⚠️ Gaby's: Kunde inte läsa sidan ({str(e)})"

def scrape_matsmak():
    try:
        url = "https://matsmak.se/lunch/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        _, day_name = get_day_info()
        
        # Matsmak har ofta sin meny i en specifik div
        content = soup.find('div', class_='entry-content') or soup
        lines = [line.strip() for line in content.get_text(separator="\n").split("\n") if len(line.strip()) > 5]
        
        menu = []
        found_day = False
        for line in lines:
            if day_name.upper() in line.upper():
                found_day = True
                continue
            if found_day:
                if any(d in line.upper() for d in ["TISDAG", "ONSDAG", "TORSDAG", "FREDAG"]):
                    break
                menu.append(f"• {line}")
        
        return "\n".join(menu) if menu else "⚠️ Ingen meny publicerad för idag."
    except Exception as e:
        return f"⚠️ Matsmak: Fel vid hämtning ({str(e)})"

async def main():
    day_idx, day_name = get_day_info()
    if day_idx is None: return 
    
    bot = Bot(token=TOKEN)
    
    # Kör de nya, förbättrade funktionerna
    gabys = scrape_gabys()
    matsmak = scrape_matsmak()
    
    msg = (
        f"🏙️ *GÅRDA LUNCH - {day_name.upper()}* 🏙️\n\n"
        f"🍸 *Gaby's (Jacy'z)*\n{gabys}\n\n"
        f"🍲 *Matsmak*\n{matsmak}\n\n"
        f"🏘️ *The Village*\n📍 [Se länk](https://www.compass-group.se/restauranger-och-menyer/ovriga-restauranger/village/)\n\n"
        f"🍽️ *Hildas*\n📍 [Se länk](https://hildasrestaurang.se/se/lunch-meny)\n\n"
        "--- \n"
        "Smaklig lunch!"
    )
    
    # Tvinga Chat ID till siffra (viktigt!)
    target_id = int(str(CHAT_ID).strip())
    
    try:
        await bot.send_message(chat_id=target_id, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
    except:
        # Fallback om specialtecken från menyerna pajar Markdown
        await bot.send_message(chat_id=target_id, text=msg.replace('*', '').replace('_', ''))

if __name__ == "__main__":
    asyncio.run(main())
