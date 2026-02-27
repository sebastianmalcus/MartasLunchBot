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
    days_sv = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
    days_en = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    idx = datetime.now().weekday()
    if idx < 5:
        return idx, days_sv[idx], days_en[idx]
    return None, None, None

def scrape_gabys(day_en):
    try:
        url = "https://jacyzhotel.com/restauranger-goteborg/gabys/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        elements = soup.find_all(['span', 'p', 'h3', 'div'])
        menu = []
        found_day = False
        all_days_en = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

        for el in elements:
            text = el.get_text(strip=True)
            if not text: continue
            
            # Mjukare matchning: Kollar om "FRIDAY" finns i texten (fungerade i din första version)
            if day_en in text.upper() and not found_day:
                found_day = True
                continue
                
            if found_day:
                # Bryt om vi ser nästa veckodag
                if any(d in text.upper() for d in all_days_en if d != day_en):
                    break
                    
                # Hård filtrering: Maträtten måste vara en rimlig längd. 
                # Säljsnacket "What's for lunch..." är över 500 tecken långt, så det ignoreras.
                if 15 < len(text) < 150:
                    menu.append(f"• {text}")
                
                # Gaby's serverar alltid exakt 3 rätter. När vi har 3, sluta leta!
                if len(menu) == 3:
                    break
        
        return "\n".join(menu) if menu else "🍴 Se menyn på Jacy'z hemsida."
    except Exception:
        return "⚠️ Gaby's: Kunde inte nå sidan."

def scrape_matsmak(day_sv):
    try:
        url = "https://matsmak.se/lunch/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Samla all text och dela på radbrytningar
        content = soup.find('div', class_='entry-content') or soup
        all_text = content.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in all_text.split('\n') if len(l.strip()) > 1]
        
        menu = []
        found_day = False
        all_days_sv = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"]

        for line in lines:
            clean_line = line.replace('\xa0', ' ')
            line_upper = clean_line.upper()
            
            # Mjukare matchning: Hittar "FREDAG" även i "FREDAGSLUNCH FÖR 99 KR!"
            if day_sv.upper() in line_upper and not found_day:
                found_day = True
                continue
            
            if found_day:
                # Sluta om vi ser en ny dag (t.ex. om vi kollar torsdag och hittar fredag)
                if any(d in line_upper for d in all_days_sv if d != day_sv.upper()):
                    break
                
                # Sök på kända prefix
                prefixes = ["KÖTT:", "FISK:", "VEG:", "BUDGET:", "VECKANS:"]
                
                if any(p in line_upper for p in prefixes):
                    menu.append(f"• {clean_line}")
                # Plocka upp andra rimliga rätter, men undvik deras fredags-erbjudande-rader
                elif len(clean_line) > 20 and ":" not in clean_line and not any(x in line_upper for x in ["BJUDER", "RABATT", "PRIS"]):
                    menu.append(f"• {clean_line}")
                    
        return "\n".join(menu) if menu else "⚠️ Hittade menyn men rätterna saknas."
    except Exception:
        return "⚠️ Matsmak: Kunde inte nå sidan."

async def main():
    day_idx, day_sv, day_en = get_day_info()
    if day_idx is None: return 
    
    bot = Bot(token=TOKEN)
    
    try:
        target_id = int(str(CHAT_ID).strip())
    except Exception:
        print("Kritisk Error: Ogiltigt Chat ID")
        return

    gabys_text = scrape_gabys(day_en)
    matsmak_text = scrape_matsmak(day_sv)
    
    msg = (
        f"🏙️ *GÅRDA LUNCH - {day_sv.upper()}* 🏙️\n\n"
        f"🍸 *Gaby's (Jacy'z)*\n{gabys_text}\n\n"
        f"🍲 *Matsmak*\n{matsmak_text}\n\n"
        f"🏘️ *The Village*\n📍 [Se länk](https://www.compass-group.se/restauranger-och-menyer/ovriga-restauranger/village/)\n\n"
        f"🍽️ *Hildas*\n📍 [Se länk](https://hildasrestaurang.se/se/lunch-meny)\n\n"
        "--- \n"
        "Smaklig lunch!"
    )
    
    try:
        await bot.send_message(chat_id=target_id, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
        print("✅ Success: Postat i gruppen!")
    except Exception:
        await bot.send_message(chat_id=target_id, text=msg.replace('*', ''))

if __name__ == "__main__":
    asyncio.run(main())
