import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

# Hämtar konfiguration från GitHub Secrets
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_day_info():
    """Returnerar index (0-4) och både svenskt och engelskt namn för dagen."""
    days_sv = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
    days_en = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    idx = datetime.now().weekday()
    if idx < 5:
        return idx, days_sv[idx], days_en[idx]
    return None, None, None

def scrape_gabys(day_en):
    """Skrapar Gaby's meny baserat på engelska veckodagar."""
    try:
        url = "https://jacyzhotel.com/restauranger-goteborg/gabys/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        elements = soup.find_all(['span', 'p', 'h3', 'div'])
        menu = []
        found_day = False
        all_days_en = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]

        for el in elements:
            text = el.get_text(strip=True)
            if not text: continue
            if text.upper() == day_en:
                found_day = True
                continue
            if found_day:
                if any(d == text.upper() for d in all_days_en if d != day_en):
                    break
                if len(text) > 10 and not any(d in text.upper() for d in all_days_en):
                    menu.append(f"• {text}")
        
        return "\n".join(menu[:4]) if menu else "🍴 Se menyn på Jacy'z hemsida (ofta buffé)."
    except Exception:
        return "⚠️ Gaby's: Kunde inte nå sidan."

def scrape_matsmak(day_sv):
    """Skrapar Matsmak baserat på din senaste Inspect-bild (svenska dagar + prefix)."""
    try:
        url = "https://matsmak.se/lunch/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Letar i entry-content där texten ligger enligt bilden
        content = soup.find('div', class_='entry-content') or soup
        lines = [l.strip() for l in content.get_text(separator="\n").split('\n') if len(l.strip()) > 2]
        
        menu = []
        found_day = False
        all_days_sv = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"]

        for line in lines:
            if line.upper() == day_sv.upper():
                found_day = True
                continue
            if found_day:
                if line.upper() in all_days_sv:
                    break
                # Fångar rader som börjar med prefixen från din bild
                if any(x in line.upper() for x in ["KÖTT:", "FISK:", "VEG:", "VECKANS:"]):
                    menu.append(f"• {line}")
                # Fångar även rader som är tydliga maträtter (längre text)
                elif len(line) > 25 and not line.startswith("VARJE DAG"):
                    menu.append(f"• {line}")
        
        return "\n".join(menu) if menu else "⚠️ Hittade menyn men rätterna saknas."
    except Exception:
        return "⚠️ Matsmak: Kunde inte nå sidan."

async def main():
    day_idx, day_sv, day_en = get_day_info()
    if day_idx is None:
        print("Det är helg!")
        return 
    
    print(f"--- STARTAR LUNCHBOT FÖR {day_sv.upper()} ---")
    
    try:
        target_id = int(str(CHAT_ID).strip())
    except:
        print(f"Kritisk Error: Ogiltigt Chat ID: {CHAT_ID}")
        return

    bot = Bot(token=TOKEN)
    
    # Hämta menyer
    gabys_text = scrape_gabys(day_en)
    matsmak_text = scrape_matsmak(day_sv)
    
    msg = (
        f"🏙️ *GÅRDA LUNCH - {day_sv.upper()}* 🏙️\n\n"
        f"🍸 *Gaby's (Jacy'z)*\n{gabys_text}\n\n"
        f"🍲 *Matsmak*\n{matsmak_text}\n\n"
        f"🏘️ *The Village*\n📍 [Se menyn här](https://www.compass-group.se/restauranger-och-menyer/ovriga-restauranger/village/)\n\n"
        f"🍽️ *Hildas*\n📍 [Se menyn här](https://hildasrestaurang.se/se/lunch-meny)\n\n"
        "--- \n"
        "Smaklig lunch!"
    )
    
    try:
        await bot.send_message(chat_id=target_id, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
        print("✅ Success: Postat i gruppen!")
    except Exception as e:
        print(f"❌ Fel vid sändning: {e}")
        # Fallback om specialtecken pajar Markdown
        await bot.send_message(chat_id=target_id, text=msg.replace('*', ''))

if __name__ == "__main__":
    asyncio.run(main())
