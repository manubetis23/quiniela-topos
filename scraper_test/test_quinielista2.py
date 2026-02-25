import requests
from bs4 import BeautifulSoup
import re

def scrape():
    url = "https://www.quinielista.es/estimacion"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36',
    }
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'lxml')
        
        # Quinielista has a main table
        tables = soup.find_all('table')
        
        for t in tables:
            rows = t.find_all('tr')
            for r in rows:
                cols = r.find_all('td')
                texts = [c.text.strip() for c in cols]
                # Usually rows look like: [1, 'Real Madrid - Barcelona', '45', '30', '25', ...]
                if len(texts) >= 5 and any(ext in texts[0] for ext in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']):
                    print(texts)
    except Exception as e:
        print(f"Error: {e}")

scrape()
