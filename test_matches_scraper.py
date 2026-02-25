from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://www.eduardolosilla.es/quiniela")
    page.wait_for_timeout(3000)
    locs = page.locator("div[class*='partido']").all_inner_texts()
    for l in locs:
        print(repr(l))
    browser.close()
