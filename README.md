# 🤖 Gårda Lunch Bot

Denna Telegram-bot körs automatiskt via GitHub Actions och hämtar dagens lunchmenyer för fyra restauranger i Gårda (Göteborg). Den sammanställer menyerna, lägger till klickbara länkar, och avslutar med ett översatt dagens citat.

## 🛠️ Så här hämtas datan (Scraping-metoder)

Eftersom alla restauranger bygger sina hemsidor på olika sätt, använder boten fyra helt olika strategier för att extrahera maten. Om en restaurang slutar fungera, kolla metoderna nedan för att felsöka.

### 1. Gaby's (Jacy'z)
* **Metod:** Rå text-extrahering via `BeautifulSoup`.
* **Hur det fungerar:** Koden laddar ner hela sidans HTML, plockar bort alla kod-taggar och letar igenom texten rad för rad. Den letar efter dagens engelska namn (t.ex. `MONDAY`). När den hittar dagen plockar den upp de följande 3 raderna som är längre än 10 tecken.
* **Felsökning:** Om Gaby's byter språk på dagarna (till svenska) eller ändrar designen helt, kan sökordet (`day_en`) eller stopp-orden (`WHAT'S FOR LUNCH`) behöva justeras.

### 2. Matsmak
* **Metod:** "Sniper-sökning" via `<strong>`-taggar.
* **Hur det fungerar:** Matsmak brukar lägga in mycket reklam ("FREDAGSLUNCH 99KR"). Koden letar upp exakt den `<strong>` (fetstilt) tagg som börjar med dagens namn (t.ex. "FREDAG"). Den klättrar sedan upp ett steg i HTML-trädet och plockar ut all text. Den filtrerar ut maten genom att leta efter prefix som `KÖTT:`, `FISK:` eller genom att sortera bort korta rader och rader som innehåller ordet "RABATT" eller "PRIS".
* **Felsökning:** Om Matsmak slutar använda fetstil för veckodagarna kommer denna metod att missa menyn.

### 3. The Village (Compass Group)
* **Metod:** CSS-klass-sökning.
* **Hur det fungerar:** Sidan byggs med Vue.js och veckans alla menyer ligger ofta inbakade i koden från start. Koden letar efter alla `<div>`-lådor som har klassen `lunch-day`. Den kollar första raden i varje låda för att se om det är rätt dag. Den rensar sedan bort deras statiska utfyllnadstext som t.ex. "LUNCH SERVERAS".
* **Felsökning:** Om Compass Group byter plattform eller döper om sina div-klasser till något annat än `lunch-day` kommer koden använda en fallback som letar efter `<h3>`-rubriker istället.

### 4. Hildas
* **Metod:** Direkt REST API-anrop ("The Hacker Way").
* **Hur det fungerar:** Hildas använder en modern headless WordPress-struktur med en animerad Slick Slider. Detta gör att maten *inte* finns i källkoden som skickas till boten, utan hämtas in via JavaScript. Istället för att skrapa HTML går koden direkt mot deras dolda databas via URL:en:
  `https://api.hildasrestaurang.se/wp-json/wp/v2/lunch?per_page=1`
  Den plockar sedan ut JSON-datan, letar upp rätt veckodag (`day_en.lower()`) och parar ihop parametrarna `title` och `text`.
* **Felsökning:** Detta är den mest stabila metoden. Den slutar bara fungera om Hildas byter webbhotell/system eller stänger sitt API.

---

## ✨ Övriga funktioner

* **Citat-maskinen:** Boten hämtar dagligen ett slumpmässigt engelskt citat från `zenquotes.io/api/random`. Den skickar därefter citatet genom Googles gratis translate-API (`translate.googleapis.com`) för att översätta det till svenska i farten, innan det skickas till Telegram.
* **Auto-Retry Session:** Boten använder en `requests.Session()` med inbyggd "Retry"-mekanism. Om en av restaurangernas webbservrar är trög eller tillfälligt blockerar anslutningen, väntar boten lite och försöker automatiskt igen upp till 3 gånger.

## 🚨 För dig som felsöker
Kör boten manuellt i GitHub Actions och klicka på steget "Run bot script". Eventuella krascher och Python-fel kommer skrivas ut i klartext där, vilket gör det enkelt att identifiera vilken restaurang som ändrat sin layout.
