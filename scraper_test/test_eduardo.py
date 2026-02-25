import requests
from bs4 import BeautifulSoup
import json
import re

def get_losilla_data():
    url = "https://www.eduardolosilla.es/quiniela"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;'
    }
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'lxml')
        
        # In Nuxt/Vue apps, state is often in window.__NUXT__
        script_text = ""
        for s in soup.find_all('script'):
            if s.string and 'window.__NUXT__' in s.string:
                script_text = s.string
                break
                
        if script_text:
            print("Found NUXT State!")
            # Basic extraction, a full parser would be better but let's try regex first
            # We are looking for something like: lae1: 45, laeX: 30, lae2: 25
            partidos = []
            
            # Find all local, visitante blocks
            matches = re.finditer(r'localNombre:"(.*?)",visitanteNombre:"(.*?)".*?porcentaje1LAE:(\d+),porcentajeXLAE:(\d+),porcentaje2LAE:(\d+)', script_text)
            for m in matches:
                partidos.append({
                    'local': m.group(1),
                    'visitante': m.group(2),
                    'lae_1': float(m.group(3)) / 100.0,
                    'lae_x': float(m.group(4)) / 100.0,
                    'lae_2': float(m.group(5)) / 100.0
                })
            
            print(json.dumps(partidos[:3], indent=2))
        else:
            print("NUXT state not found.")
            
    except Exception as e:
        print(f"Err: {e}")

get_losilla_data()
