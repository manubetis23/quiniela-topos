from playwright.sync_api import sync_playwright

def find_matches():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.eduardolosilla.es/quiniela", timeout=20000)
        page.wait_for_timeout(3000)
        
        # In Eduardo Losilla the matches are usually inside a grid. Let's find elements with class that might contain teams.
        # Let's just print all rows of tables:
        rows = page.locator("tr").all_inner_texts()
        print(f"Encontradas {len(rows)} filas de tabla")
        for r in rows[:30]:
            print(r.replace("\n", " | "))
            
        print("--- Alternativamente, divs con 'partido' ---")
        locs = page.locator("div[class*='partido']").all_inner_texts()
        for l in locs[:10]:
            print(l.replace("\n", " | "))
            
        browser.close()

if __name__ == "__main__":
    find_matches()
