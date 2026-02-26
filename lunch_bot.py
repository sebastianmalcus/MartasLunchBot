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
    """Skrapar Gaby's meny (Jacy'z) baserat på engelska veckodagar."""
    try:
        url = "https://jacyzhotel.com/restauranger-goteborg/gabys/"
        headers = {'User-Agent': 'Mozilla/5.0'}
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
                if len(text) > 15 and not any(d in text.upper() for d in all_days_en):
                    menu.append(f"• {text}")
        
        return "\n".join(menu[:4]) if menu else "🍴 Se menyn på Jacy'z hemsida."
    except:
        return "⚠️ Gaby's: Kunde inte nå sidan."

def scrape_matsmak(day_sv):
    """Skrapar Matsmak genom att hantera <br>-taggar och prefix som BUDGET/KÖTT/FISK."""
    try:
        url = "https://matsmak.se/lunch/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Matsmak använder <br> för radbrytningar inuti <p>.
        # separator="\n" gör att vi får ut rätterna rad för rad.
        content = soup.find('div', class_='entry-content') or soup
        all_text = content.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in all_text.split('\n') if len(l.strip()) > 1]
        
        menu = []
        found_day = False
        all_days_sv = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"]

        for line in lines:
            # Matchar mot rubriken, t.ex. "TORSDAG"
            if line.upper() == day_sv.upper():
                found_day = True
                continue
            
            if found_day:
                # Sluta om vi når nästa dag
                if line.upper() in all_days_sv:
                    break
                
                # Prefix från din senaste skärmdump
                prefixes = ["KÖTT:", "FISK:", "VEG:", "BUDGET:", "VECKANS:", "VEG:"]
                
                # Tvätta texten från specialtecken (som non-breaking spaces)
                clean_line = line.replace('\xa0', ' ')
                
                if any(p in clean_line.upper() for p in prefixes):
                    menu.append(f"• {clean_line}")
                # Fångar rader som är tydliga maträtter men saknar prefix (minst 20 tecken)
                elif len(clean_line) > 20 and ":" not in clean_line:
                    menu.append(f"• {clean_line}")
        
        return "\n".join(menu) if menu else "⚠️ Hittade menyn men rätterna saknas."
    except:
        return "⚠️ Matsmak: Kunde inte nå sidan."

async def main():
    day_idx, day_sv, day_en = get_day_info()
    if day_idx is None: return 
    
    bot = Bot(token=TOKEN)
    
    # Säkerställ att ID är en ren siffra för Telegram API
    try:
        target_id = int(str(CHAT_ID).strip())
    except:
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
    except:
        # Fallback om specialtecken pajar Markdown-formateringen
        await bot.send_message(chat_id=target_id, text=msg.replace('*', ''))

if __name__ == "__main__":
    asyncio.run(main())
