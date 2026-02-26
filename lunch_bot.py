def scrape_gabys():
    try:
        url = "https://jacyzhotel.com/restauranger-goteborg/gabys/"
        # Vi lägger till en User-Agent för att se ut som en vanlig webbläsare
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        _, day_name = get_day_info()
        
        # Vi hämtar all text och letar efter rader som kommer efter dagens namn
        text_content = soup.get_text(separator="\n", strip=True)
        lines = text_content.split('\n')
        
        menu = []
        found_day = False
        for line in lines:
            if day_name.upper() in line.upper():
                found_day = True
                continue
            if found_day:
                # Om raden är för kort eller innehåller nästa dag, sluta
                if any(d in line.upper() for d in ["TISDAG", "ONSDAG", "TORSDAG", "FREDAG", "LÖRDAG"]):
                    break
                if len(line) > 10: # En rimlig maträtt är oftast längre än 10 tecken
                    menu.append(f"• {line}")
        
        return "\n".join(menu[:3]) if menu else "🍴 Buffé/Meny finns på plats. Se länk!"
    except:
        return "❌ Kunde inte nå Jacy'z sajt just nu."

def scrape_matsmak():
    try:
        url = "https://matsmak.se/lunch/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        _, day_name = get_day_info()

        # Matsmak har ibland rätterna i 'p'-taggar efter en rubrik
        all_text = soup.get_text(separator="\n", strip=True)
        lines = all_text.split('\n')
        
        menu = []
        capture = False
        for line in lines:
            if day_name.upper() in line.upper():
                capture = True
                continue
            if capture:
                if any(d in line.upper() for d in ["TISDAG", "ONSDAG", "TORSDAG", "FREDAG"]):
                    break
                if len(line) > 15:
                    menu.append(f"• {line}")
        
        return "\n".join(menu) if menu else "⚠️ Menyn ej uppdaterad på sajten."
    except:
        return "❌ Kunde inte nå Matsmak."
