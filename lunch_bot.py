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
        
        # Läs in hela sidans text uppifrån och ner
        lines = [line.strip() for line in soup.get_text(separator="\n").split("\n") if line.strip()]
        
        menu = []
        found_day = False
        all_days_en = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

        for line in lines:
            upper_line = line.upper()
            
            # 1. Hitta exakt rätt veckodag
            if upper_line == day_en:
                found_day = True
                continue
                
            if found_day:
                # 2. Sluta leta om vi snubblar in på nästa veckodag
                if upper_line in all_days_en:
                    break
                    
                # 3. SPÄRR: Stanna direkt om vi når deras säljsnack (sidfoten)
                if "WHAT'S FOR LUNCH" in upper_line or "JACY'Z" in upper_line:
                    break
                    
                # 4. Plocka allt som ser ut som en maträtt (över 10 tecken)
                if len(line) > 10:
                    menu.append(f"• {line}")
                    
                # 5. SPÄRR: Gaby's har alltid max 3 rätter. Sen är vi klara!
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
        
        content = soup.find('div', class_='entry-content') or soup
        all_text = content.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in all_text.split('\n') if len(l.strip()) > 1]
        
        menu = []
        found_day = False
        all_days_sv = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"]

        for line in lines:
            clean_line = line.replace('\xa0', ' ')
            line_upper = clean_line.upper()
            
            if day_sv.upper() in line_upper and not found_day:
                found_day = True
                continue
            
            if found_day:
                if any(d in line_upper for d in all_days_sv if d != day_sv.upper()):
                    break
                
                prefixes = ["KÖTT:", "FISK:", "VEG:", "BUDGET:", "VECKANS:"]
                
                if any(p in line_upper for p in prefixes):
                    menu.append(f"• {clean_line}")
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
    except Exception:
        await bot.send_message(chat_id=target_id, text=msg.replace('*', ''))

if __name__ == "__main__":
    asyncio.run(main())
