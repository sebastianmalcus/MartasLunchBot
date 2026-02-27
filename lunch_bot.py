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
        url = "https://matsmak.se/dagens-lunch/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, timeout=15, headers=headers)
        res.raise_for_status() 
        
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        menu = []
        
        for strong in soup.find_all('strong'):
            strong_text = strong.get_text(strip=True).upper()
            
            if strong_text.startswith(day_sv.upper()):
                parent_block = strong.parent
                
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
        return f"⚠️ Systemfel på Matsmak: {e}"

def scrape_village(day_sv):
    try:
        url = "https://www.compass-group.se/restauranger-och-menyer/ovriga-restauranger/village/village-restaurang/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, timeout=15, headers=headers)
        res.raise_for_status()
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        menu = []
        day_blocks = soup.find_all('div', class_=lambda c: c and 'lunch-day' in c)
        
        if not day_blocks:
            for h3 in soup.find_all(['h3', 'h2']):
                if h3.get_text(strip=True).upper().startswith(day_sv.upper()):
                    day_blocks = [h3.parent]
                    break

        for block in day_blocks:
            text = block.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            if lines and lines[0].upper().startswith(day_sv.upper()):
                for line in lines[1:]: 
                    if "LUNCH SERVERAS" in line.upper() or len(line) < 15:
                        continue
                    menu.append(f"• {line}")
                break 
                
        return "\n".join(menu) if menu else "⚠️ Hittade inte dagens meny på The Village."
    except Exception as e:
        return f"⚠️ Systemfel på The Village: {e}"

def scrape_hildas(day_sv):
    """Skrapar Hildas genom att leta efter rätt h3-rubrik, oavsett om de lagt till extratext."""
    try:
        url = "https://hildasrestaurang.se/se/lunch-meny"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, timeout=15, headers=headers)
        res.raise_for_status()
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        menu = []
        
        # Leta igenom alla <h3>-rubriker på sidan
        for h3 in soup.find_all('h3'):
            h3_text = h3.get_text(strip=True).upper()
            
            # Om dagens namn (t.ex. "FREDAG") FINNS i rubriken (mjukare matchning)
            if day_sv.upper() in h3_text:
                
                # Klättra upp ett steg för att hitta hela lådan
                wrapper = h3.find_parent('div', class_='menu_wrapper')
                if not wrapper:
                    wrapper = h3.parent # Fallback om klassnamnet ändrats
                
                # Leta specifikt efter <p>-taggarna du visade i bilden
                titles = wrapper.find_all('p', class_='menus_title')
                contents = wrapper.find_all('p', class_='menus_content')
                
                if titles and contents:
                    # Matcha ihop dem snyggt
                    for t, c in zip(titles, contents):
                        t_text = t.get_text(strip=True)
                        c_text = c.get_text(strip=True)
                        if c_text:
                            menu.append(f"• *{t_text}:* {c_text}")
                else:
                    # Nödlösning: Plocka all rimlig text från lådan
                    for p in wrapper.find_all('p'):
                        p_text = p.get_text(strip=True)
                        if p_text and len(p_text) > 10:
                            menu.append(f"• {p_text}")
                
                # Om vi lyckades fylla på med mat, avbryt (för att undvika dolda kloner i karusellen)
                if menu:
                    break
                
        return "\n".join(menu) if menu else "⚠️ Hittade inte dagens meny på Hildas."
    except Exception as e:
        return f"⚠️ Systemfel på Hildas: {e}"

async def main():
    day_idx, day_sv, day_en = get_day_info()
    if day_idx is None: return 
    
    bot = Bot(token=TOKEN)
    
    try:
        target_id = int(str(CHAT_ID).strip())
    except Exception:
        print("Kritisk Error: Ogiltigt Chat ID")
        return

    # Ladda ner alla menyer
    gabys_text = scrape_gabys(day_en)
    matsmak_text = scrape_matsmak(day_sv)
    village_text = scrape_village(day_sv)
    hildas_text = scrape_hildas(day_sv)
    
    # Det kompletta resultatet
    msg = (
        f"🏙️ *GÅRDA LUNCH - {day_sv.upper()}* 🏙️\n\n"
        f"🍸 *Gaby's (Jacy'z)*\n{gabys_text}\n\n"
        f"🍲 *Matsmak*\n{matsmak_text}\n\n"
        f"🏘️ *The Village*\n{village_text}\n\n"
        f"🍽️ *Hildas*\n{hildas_text}\n\n"
        "--- \n"
        "Smaklig lunch!"
    )
    
    try:
        await bot.send_message(chat_id=target_id, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
        print("✅ Success: Skickat med alla fyra restauranger!")
    except Exception:
        # Om Hildas nya *Fetstil* bråkar med Telegrams formatteringsregler
        await bot.send_message(chat_id=target_id, text=msg.replace('*', ''))

if __name__ == "__main__":
    asyncio.run(main())
