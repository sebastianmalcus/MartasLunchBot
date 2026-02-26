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
    return idx, days_sv[idx] if idx < 5 else (None, None)

def scrape_gabys():
    try:
        # Gaby's ligger på Jacy'z hemsida
        url = "https://jacyzhotel.com/restauranger-goteborg/gabys/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        
        day_idx, day_name = get_day_info()
        
        # Jacy'z menyer ligger ofta i artiklar eller specifika sektioner
        # Vi letar efter texten för rätt dag
        menu_section = soup.find_all(['p', 'div', 'h3', 'h4'])
        found_menu = []
        start_collecting = False
        
        for element in menu_section:
            text = element.get_text(strip=True)
            if day_name.upper() in text.upper():
                start_collecting = True
                continue
            if start_collecting:
                # Om vi stöter på nästa dag, sluta samla
                next_days = ["TISDAG", "ONSDAG", "TORSDAG", "FREDAG", "LÖRDAG"]
                if any(d in text.upper() for d in next_days if d != day_name.upper()):
                    break
                if len(text) > 5:
                    found_menu.append(f"• {text}")
        
        return "\n".join(found_menu) if found_menu else "Hittade menyn, men kunde inte extrahera rätterna. Se länk!"
    except Exception as e:
        return f"❌ Fel Gaby's: {str(e)}"

def scrape_matsmak():
    try:
        url = "https://matsmak.se/lunch/"
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        _, day_name = get_day_info()
        
        # Matsmak brukar ha rätterna i en <div class="entry-content">
        content = soup.find('div', class_='entry-content')
        if not content: return "⚠️ Kunde inte hitta meny-containern."
        
        menu_text = content.get_text(separator="\n", strip=True)
        lines = menu_text.split('\n')
        
        day_menu = []
        capture = False
        for line in lines:
            if day_name.upper() in line.upper():
                capture = True
                continue
            if capture:
                # Om nästa rad är en ny dag, avbryt
                if any(d in line.upper() for d in ["TISDAG", "ONSDAG", "TORSDAG", "FREDAG"]):
                    break
                if len(line.strip()) > 10: # Undvik korta rader/skräp
                    day_menu.append(f"• {line.strip()}")
        
        return "\n".join(day_menu) if day_menu else "⚠️ Hittade ingen meny för idag."
    except Exception as e:
        return f"❌ Fel Matsmak: {str(e)}"

def scrape_village():
    try:
        # The Village - Compass Group
        url = "https://compass.mashie.matildaplatform.com/public/app/village/87c47671"
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Samma logik som din förra bot för Compass
        day_panel = soup.find('div', class_='panel-primary') or soup.find('div', class_='panel')
        if not day_panel: return "⚠️ Hittade inte dagens meny."
        
        items = day_panel.find_all('div', class_='app-daymenu-name')
        return "\n".join([f"• {i.get_text(strip=True)}" for i in items])
    except:
        return "❌ Fel The Village."

async def main():
    day_idx, day_name = get_day_info()
    if day_idx is None or day_idx >= 5: return 
    
    bot = Bot(token=TOKEN)
    
    msg = (
        f"🏙️ *GÅRDA LUNCH - {day_name.upper()}* 🏙️\n\n"
        f"🍸 *Gaby's (Jacy'z)*\n{scrape_gabys()}\n\n"
        f"🍲 *Matsmak*\n{scrape_matsmak()}\n\n"
        f"🏘️ *The Village*\n{scrape_village()}\n\n"
        f"🍽️ *Hildas*\n📍 [Se menyn här](https://hildasrestaurang.se/se/lunch-meny)\n\n"
        "--- \n"
        "Smaklig lunch!"
    )
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
    except:
        # Fallback utan formatering om något tecken krockar med Markdown
        await bot.send_message(chat_id=CHAT_ID, text=msg.replace('*', '').replace('_', ''))

if __name__ == "__main__":
    asyncio.run(main())
