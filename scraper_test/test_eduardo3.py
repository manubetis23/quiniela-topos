import requests
from bs4 import BeautifulSoup
import json
import re

url = "https://www.eduardolosilla.es/quiniela"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'lxml')

# Find variables inside scripts
for s in soup.find_all('script'):
    if s.string and ('porcentajeLAE' in s.string or 'porcentaje1LAE' in s.string):
        print("Found matching text in script:")
        print(s.string[:200])
        # Try to find all LAE matches
        matches = re.finditer(r'localNombre:([\'"a-zA-Z\s]+),visitanteNombre:([\'"a-zA-Z\s]+).*?porcentaje1LAE:(\d+),porcentajeXLAE:(\d+),porcentaje2LAE:(\d+)', s.string, flags=re.IGNORECASE)
        for m in matches:
            print(f"{m.group(1)} vs {m.group(2)}: {m.group(3)}-{m.group(4)}-{m.group(5)}")

