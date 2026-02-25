import requests
import json

def get_lae_public_data():
    # Another open JSON service from LAE
    url = "https://www.loteriasyapuestas.es/servicios/buscadoresorteos?idSorteo=LAQU"
    url2 = "https://www.loteriasyapuestas.es/servicios/fechasorteadas?idTpe=LAQU"
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        req = requests.get(url2, headers=headers)
        data = req.json()
        print(data[0])
    except Exception as e:
        print(f"Error v2: {e}")

get_lae_public_data()
