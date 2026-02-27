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
            
            # Starta om vi hittar dagen
            if text.upper().startswith(day_en):
                found_day = True
                continue
                
            if found_day:
                # Sluta om vi når nästa dag
                if any(text.upper().startswith(d) for d in all_days_en if d != day_en):
                    break
                    
                # FIX FÖR ONÖDIG TEXT: Filtrerar bort säljsnack genom att max tillåta 130 tecken per rad
                if 15 < len(text) < 130 and not any(d in text.upper() for d in all_days_en):
                    menu.append(f"• {text}")
        
        # Begränsar till max 3 rätter så vi slipper eventuellt eftersläpande skräp
        return "\n".join(menu[:3]) if menu else "🍴 Se menyn på Jacy'z hemsida."
    except Exception:
        return "⚠️ Gaby's: Kunde inte nå sidan."

def scrape_matsmak(day_sv):
    try:
        url = "https://matsmak.se/lunch/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Matsmak har varje dagsmeny i egna <p>-taggar enligt din Inspect-bild
        paragraphs = soup.find_all('p')
        menu = []

        for p in paragraphs:
            # Separera innehållet med radbrytning
            text = p.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 1]
            
            if not lines: continue
            
            # Kollar om någon av de första raderna i stycket börjar med dagens namn
            # (Fångar upp "FREDAG - Vi bjuder på..." och "FREDAGSLUNCH")
            if any(line.upper().startswith(day_sv.upper()) for line in lines[:2]):
                
                # Vi har hittat rätt paragraf! Läs rätterna:
                for line in lines:
                    clean_line = line.replace('\xa0', ' ')
                    prefixes = ["KÖTT:", "FISK:", "VEG:", "BUDGET:", "VECKANS:"]
                    
                    if any(p in clean_line.upper() for p in prefixes):
                        menu.append(f"• {clean_line}")
                    # Plocka långa rader som ser ut som mat, men undvik deras fredags-säljsnack
                    elif len(clean_line) > 25 and ":" not in clean_line and "BJUDER" not in clean_line.upper():
                        menu.append(f"• {clean_line}")
                
                # När vi hittat och läst dagens paragraf behöver vi inte leta mer
                break
                
        return "\n".join(menu) if menu else "⚠️ Hittade menyn men kunde inte extrahera rätterna."
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
