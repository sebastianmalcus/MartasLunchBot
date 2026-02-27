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
        
        lines = [line.strip() for line in soup.get_text(separator="\n").split("\n") if line.strip()]
        
        menu = []
        found_day = False
        all_days_en = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

        for line in lines:
            upper_line = line.upper()
            
            if upper_line == day_en:
                found_day = True
                continue
                
            if found_day:
                if upper_line in all_days_en:
                    break
                    
                if "WHAT'S FOR LUNCH" in upper_line or "JACY'Z" in upper_line:
                    break
                    
                if len(line) > 10:
                    menu.append(f"• {line}")
                    
                if len(menu) == 3:
                    break
        
        return "\n".join(menu) if menu else "🍴 Se menyn på Jacy'z hemsida."
    except Exception:
        return "⚠️ Gaby's: Kunde inte nå sidan."

def scrape_matsmak(day_sv):
    try:
        url = "https://matsmak.se/lunch/"
        # Uppdaterad och kraftfullare User-Agent för att undvika blockeringar
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, timeout=15, headers=headers)
        # Säg till om vi blir blockerade av servern (t.ex. 403 Forbidden)
        res.raise_for_status() 
        
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        menu = []
        
        for strong in soup.find_all('strong'):
            strong_text = strong.get_text(strip=True).upper()
            
            if strong_text.startswith(day_sv.upper()):
                parent_block = strong.parent
                
                # Om parent_block är null (osannolikt, men säkrast att kolla)
                if not parent_block:
                    continue
                    
                lines = [l.strip() for l in parent_block.get_text(separator="\n").split('\n') if len(l.strip()) > 2]
                
                for line in lines:
                    clean_line = line.replace('\xa0', ' ')
                    line_upper = clean_line.upper()
                    
                    if line_upper.startswith(day_sv.upper()):
                        continue
                        
                    prefixes = ["KÖTT:", "FISK:", "VEG:", "BUDGET:", "VECKANS:"]
                    
                    if any(p in line_upper for p in prefixes):
                        menu.append(f"• {clean_line}")
                    elif len(clean_line) > 20 and ":" not in clean_line and "RABATT" not in line_upper and "PRIS" not in line_upper and "BJUDER" not in line_upper:
                        menu.append(f"• {clean_line}")
                
                if menu:
                    break
                    
        return "\n".join(menu) if menu else "⚠️ Hittade inte dagens rubrik på Matsmak."
    except Exception as e:
        # Nu skickar vi det EXAKTA felmeddelandet till chatten så vi slipper gissa
        return f"⚠️ Systemfel på Matsmak: {e}"

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
