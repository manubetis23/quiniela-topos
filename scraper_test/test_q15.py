import requests
from bs4 import BeautifulSoup

def scrape_q15():
    url = "https://www.quiniela15.com/porcentajes-estimados-quiniela"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'lxml')
        
        # Encuentra la tabla de porcentajes
        tables = soup.find_all('table')
        for t in tables:
            if 'Porcentajes' in t.text or 'LAE' in t.text or '1' in t.text:
                rows = t.find_all('tr')
                for r in rows:
                    cols = r.find_all(['td', 'th'])
                    print([c.text.strip() for c in cols])
                break
                
    except Exception as e:
        print(f"Error Q15: {e}")

scrape_q15()
