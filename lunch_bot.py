import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

def get_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def scrape_gabys(day_en):
    try:
        url = "https://jacyzhotel.com/restauranger-goteborg/gabys/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = get_session().get(url, timeout=15, headers=headers)
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
                if upper_line in all_days_en: break
                if "WHAT'S FOR LUNCH" in upper_line or "JACY'Z" in upper_line: break
                if len(line) > 10: menu.append(f"• {line}")
                if len(menu) == 3: break
        
        return "\n".join(menu) if menu else "🍴 Se menyn på Jacy'z hemsida."
    except Exception:
        return "⚠️ Gaby's: Kunde inte nå sidan."

def scrape_matsmak(day_sv):
    try:
        url = "https://matsmak.se/dagens-lunch/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        res = get_session().get(url, timeout=20, headers=headers)
        res.raise_for_status() 
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        menu = []
        for strong in soup.find_all('strong'):
            strong_text = strong.get_text(strip=True).upper()
            if strong_text.startswith(day_sv.upper()):
                parent_block = strong.parent
                if not parent_block: continue
                lines = [l.strip() for l in parent_block.get_text(separator="\n").split('\n') if len(l.strip()) > 2]
                for line in lines:
                    clean_line = line.replace('\xa0', ' ')
                    line_upper = clean_line.upper()
                    if line_upper.startswith(day_sv.upper()): continue
                    prefixes = ["KÖTT:", "FISK:", "VEG:", "BUDGET:", "VECKANS:"]
                    if any(p in line_upper for p in prefixes):
                        menu.append(f"• {clean_line}")
                    elif len(clean_line) > 20 and ":" not in clean_line and "RABATT" not in line_upper and "PRIS" not in line_upper and "BJUDER" not in line_upper:
                        menu.append(f"• {clean_line}")
                if menu: break
        return "\n".join(menu) if menu else "⚠️ Hittade inte dagens rubrik på Matsmak."
    except requests.exceptions.Timeout: return "⚠️ Matsmak: Sidan tog för lång tid att svara."
    except requests.exceptions.ConnectionError: return "⚠️ Matsmak: Servern blockerar anslutningen."
    except Exception: return "⚠️ Systemfel på Matsmak."

def scrape_village(day_sv):
    try:
        url = "https://www.compass-group.se/restauranger-och-menyer/ovriga-restauranger/village/village-restaurang/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = get_session().get(url, timeout=15, headers=headers)
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
                    if "LUNCH SERVERAS" in line.upper() or len(line) < 15: continue
                    menu.append(f"• {line}")
                break 
        return "\n".join(menu) if menu else "⚠️ Hittade inte dagens meny på The Village."
    except Exception: return "⚠️ Systemfel på The Village."

def scrape_hildas(day_sv):
    """Debug-läge och en extremt grundläggande text-skrapning för Hildas."""
    try:
        url = "https://hildasrestaurang.se/se/lunch-meny"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = get_session().get(url, timeout=15, headers=headers)
        res.raise_for_status()
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        # --- GITHUB ACTIONS DEBUGGING ---
        print("\n" + "="*40)
        print(f"🕵️ DEBUG HILDAS FÖR: {day_sv.upper()}")
        print("="*40)
        if day_sv.upper() in res.text.upper():
            print(f"✅ Ordet '{day_sv}' FINNS i den råa källkoden!")
        else:
            print(f"❌ Ordet '{day_sv}' SAKNAS HELT i råkoden. Datan laddas via API/JS.")
            
        test_word = soup.find(string=lambda t: t and "Fläskkött" in t)
        if test_word:
            print(f"✅ Hittade ordet 'Fläskkött'. Dess omslutande tagg är:\n{test_word.find_parent()}")
        else:
            print("❌ Hittade inte ens ordet 'Fläskkött' i källkoden.")
        print("="*40 + "\n")
        # --------------------------------

        menu = []
        # Fallback: Den dummaste men mest robusta metoden. Plocka all ren text på sidan.
        lines = [line.strip() for line in soup.get_text(separator="\n").split("\n") if line.strip()]
        found_day = False
        all_days = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"]

        for line in lines:
            line_upper = line.upper()
            # Om raden är "
