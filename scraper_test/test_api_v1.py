import requests
import json

def get_quiniela_v1():
    url = "https://www.loteriasyapuestas.es/servicios/buscadoresorteos?idSorteo=LAQU"
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        print("Buscador:", json.dumps(data[:1], indent=2))
        
    except Exception as e:
        print(f"Buscador err: {e}")

get_quiniela_v1()
