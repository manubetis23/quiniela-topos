import requests
from bs4 import BeautifulSoup
import json
import re

def scrape():
    url = "https://www.eduardolosilla.es/quiniela/estimacion"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
    }
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'lxml')
        
        # In Nuxt apps, the initial state is injected in window.__NUXT__
        script_text = ""
        for s in soup.find_all('script'):
            if s.string and 'window.__NUXT__' in s.string:
                script_text = s.string
                break
                
        if script_text:
            print("Found NUXT Script tag.")
            # Let's use regex to find the percentages. They usually look like:
            # porcentaje1LAE: 45, porcentajeXLAE: 30, porcentaje2LAE: 25
            
            # Find the matches array
            partidos = []
            
            # The structure is tightly minified
            names_iter = re.finditer(r'localNombre:"(.*?)",visitanteNombre:"(.*?)"', script_text)
            
            # We also need to find percentages
            perc_iter = re.finditer(r'porcentaje1LAE:(\d+),porcentajeXLAE:(\d+),porcentaje2LAE:(\d+)', script_text)
            
            names = list(names_iter)
            percs = list(perc_iter)
            
            if len(names) > 0 and len(names) == len(percs):
                for i in range(min(15, len(names))):
                    local = names[i].group(1)
                    visitante = names[i].group(2)
                    p1 = float(percs[i].group(1)) / 100.0
                    px = float(percs[i].group(2)) / 100.0
                    p2 = float(percs[i].group(3)) / 100.0
                    
                    partidos.append({
                        'local': local,
                        'visitante': visitante,
                        'lae_1': p1,
                        'lae_x': px,
                        'lae_2': p2
                    })
                    
                print(json.dumps(partidos[:3], indent=2))
                return True
            else:
                print(f"Mismatch: found {len(names)} names and {len(percs)} percentages.")
    except Exception as e:
        print(f"Error: {e}")
        
    return False

scrape()
