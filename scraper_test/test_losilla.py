import requests
from bs4 import BeautifulSoup
import json

def get_losilla_percentages():
    url = "https://www.eduardolosilla.es/quiniela"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching {url}...")
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'lxml')
        
        partidos = []
        
        # In Eduardolosilla, percentages are usually within the 'jornada-partidos' or similar
        # Let's inspect scripts for a JSON payload as Vue/React apps inject state
        for script in soup.find_all('script'):
            if script.string and 'window.__INITIAL_STATE__' in script.string:
                print("Found initial state!")
                # Extract JSON
                start = script.string.find('{')
                end = script.string.rfind('}') + 1
                state_json = json.loads(script.string[start:end])
                
                # Check for matches
                if 'quiniela' in state_json and 'jornada' in state_json['quiniela']:
                    partidos_data = state_json['quiniela']['jornada'].get('partidos', [])
                    for p in partidos_data:
                        partidos.append({
                            'id': p.get('numero'),
                            'local': p.get('localNombre'),
                            'visitante': p.get('visitanteNombre'),
                            'lae_1': p.get('porcentaje1LAE'),
                            'lae_X': p.get('porcentajeXLAE'),
                            'lae_2': p.get('porcentaje2LAE')
                        })
                    break
        
        print(json.dumps(partidos, indent=2))
        
    except Exception as e:
        print(f"Error scraping losilla: {e}")

get_losilla_percentages()
