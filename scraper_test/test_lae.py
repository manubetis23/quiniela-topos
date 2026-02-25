import requests
import json

def get_lae_percentages():
    url = "https://www.loteriasyapuestas.es/es/la-quiniela/escrutinios"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    # Intento 2: Usar API JSON directa si existe, o buscar los IDs de sorteos activos
    api_sorteos = "https://www.loteriasyapuestas.es/servicios/fechasorteadas?idTpe=LAQU&anio=2025"
    try:
        res = requests.get(api_sorteos, headers=headers)
        fechas = res.json()
        print("Sorteos activos:", fechas[:2])
        
        ultima_fecha = fechas[0]['fechaSorteo']
        
        api_escrutinio = f"https://www.loteriasyapuestas.es/servicios/escrutinio?idTpe=LAQU&fechaSorteo={ultima_fecha}"
        res_esc = requests.get(api_escrutinio, headers=headers)
        print("Escrutinio:")
        print(json.dumps(res_esc.json(), indent=2))
        
    except Exception as e:
        print(e)
        
get_lae_percentages()
