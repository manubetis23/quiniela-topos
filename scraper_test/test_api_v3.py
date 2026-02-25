import requests
import json

def get_lae_public_data():
    # Another open JSON service from LAE without User-Agent checks
    url = "https://www.loteriasyapuestas.es/servicios/fechasorteadas"
    params = {'idTpe': 'LAQU'}
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'curl/7.68.0' # Curl often bypasses basic filters
    }
    
    try:
        req = requests.get(url, params=params, headers=headers)
        print(req.status_code)
        if req.status_code == 200:
            data = req.json()
            print(data[0])
    except Exception as e:
        print(f"Error v3: {e}")

get_lae_public_data()
