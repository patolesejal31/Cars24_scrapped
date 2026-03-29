import csv
import time
from playwright.sync_api import sync_playwright

def scrape_cars24():
    results = []
    url = "https://www.cars24.com/buy-used-cars-ahmedabad/"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="networkidle")

        # Wait for the grid to appear
        page.wait_for_selector("div.styles_outer__NTVth", timeout=15000)

        # -------- SCROLLING --------
        print("Scrolling to load 100+ cars...")
        for i in range(25):
            page.evaluate("window.scrollBy(0, 1500)")
            time.sleep(1) 

        # -------- JAVASCRIPT EXTRACTION (Corrected .push()) --------
        print("Extracting data from loaded cards...")
        
        raw_data = page.evaluate("""() => {
            const cards = document.querySelectorAll('div.styles_outer__NTVth');
            const data = [];
            cards.forEach(card => {
                // Name is usually in the first span or h3
                const name = card.querySelector('span')?.innerText || card.querySelector('h3')?.innerText || "N/A";
                
                // Price & EMI via Regex on the card's full text
                const fullText = card.innerText;
                const priceMatch = fullText.match(/\\d+\\.?\\d*\\s?(lakh|crore)/i);
                const emiMatch = fullText.match(/EMI\\s?₹?\\d+,?\\d*\\/m/i);
                
                const specs = card.querySelectorAll('ul p, ul li');
                const km = specs[0]?.innerText || "N/A";
                const fuel = specs[1]?.innerText || "N/A";
                const trans = specs[2]?.innerText || "N/A";
                
                const link = card.closest('a')?.href || "N/A";
                

                // USE .push() NOT .append()
                data.push({
                    name: name.trim(),
                    price: priceMatch ? priceMatch[0] : "N/A",
                    emi: emiMatch ? emiMatch[0] : "N/A",
                    kilometer: km.trim(),
                    fuel: fuel.trim(),
                    transmission: trans.trim(),
                    link: link
                });
            });
            return data;
        }""")

        # Filter out duplicates and cleanup
        seen_links = set()
        for item in raw_data:
            if item['link'] not in seen_links and item['name'] != "N/A":
                results.append(item)
                seen_links.add(item['link'])

        browser.close()
    return results

# -------- SAVE TO CSV --------
cars_data = scrape_cars24()

if cars_data:
    filename = "cars24_ahmedabad.csv"
    keys = cars_data[0].keys()
    with open(filename, 'wb') as f: # Using standard open with encoding
        pass 
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(cars_data)
    print(f"\nSUCCESS: Saved {len(cars_data)} unique cars to {filename}!")
else:
    print("\nERROR: No data found.")