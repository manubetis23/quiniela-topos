import requests
import json

def get_losilla_api():
    url = "https://www.eduardolosilla.es/api/quiniela/jornada"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept': 'application/json'
    }
    
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        partidos = data.get('partidos', [])
        
        parsed = []
        for p in partidos:
            parsed.append({
                'local': p.get('localNombre'),
                'visitante': p.get('visitanteNombre'),
                'lae_1': p.get('porcentaje1LAE', 0) / 100.0,
                'lae_x': p.get('porcentajeXLAE', 0) / 100.0,
                'lae_2': p.get('porcentaje2LAE', 0) / 100.0
            })
            
        print(json.dumps(parsed[:3], indent=2))
        
    except Exception as e:
        print(f"Err: {e}")

get_losilla_api()
