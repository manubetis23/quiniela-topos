from playwright.sync_api import sync_playwright

def get_matches():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.eduardolosilla.es/quiniela", timeout=15000)
        
        # In Eduardo Losilla, matches are usually inside a table or specific divs
        # Let's extract all text and find the pairings.
        locators = page.locator(".partido-nombre")
        count = locators.count()
        if count > 0:
            for i in range(count):
                print(locators.nth(i).inner_text())
        else:
            # try finding 15 rows
            rows = page.locator(".filQnl")
            rcount = rows.count()
            for i in range(min(rcount, 15)):
                print(rows.nth(i).inner_text())
                
        browser.close()

try:
    get_matches()
except Exception as e:
    print(e)
