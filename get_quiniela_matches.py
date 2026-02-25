import re

def obtener_jornada_quiniela():
    from playwright.sync_api import sync_playwright
    matches_dict = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.eduardolosilla.es/quiniela", timeout=20000)
            page.wait_for_timeout(3000)
            
            # Buscar divs de partidos
            locs = page.locator("div[class*='partido']").all_inner_texts()
            
            for l in locs:
                line = l.replace("\n", " | ")
                parts = line.split(" | ")
                if len(parts) > 1 and " - " in parts[1]:
                    # Extraer número de partido (1-15) del primer campo
                    num_str = re.sub(r'[^0-9]', '', parts[0].strip())
                    match_num = int(num_str) if num_str else None
                    
                    match_str = parts[1].strip()
                    equipos = match_str.split(" - ")
                    if len(equipos) == 2 and match_num is not None:
                        home, away = equipos[0].strip(), equipos[1].strip()
                        match_format = f"{home} - {away}"
                        if match_num not in matches_dict:
                            matches_dict[match_num] = match_format
                        
                        if len(matches_dict) == 15:
                            break
                            
            browser.close()
    except Exception as e:
        print(f"Error scraping jornada: {e}")
    
    # Ordenar por número de partido (1-15)
    ordered = [matches_dict[i] for i in sorted(matches_dict.keys())]
    return clean_names(ordered)

def clean_names(matches_list):
    # Diccionario inverso para cuadrar con nuestra DB
    # Losilla usa R.MADRID, AT.MADRID, ATH.CLUB, etc.
    name_map = {
        'R.MADRID': 'Real Madrid',
        'REAL MADRID': 'Real Madrid',
        'BARCELONA': 'Barcelona',
        'AT.MADRID': 'Ath Madrid',
        'ATLETICO MADRID': 'Ath Madrid',
        'VILLARREAL': 'Villarreal',
        'ATH.CLUB': 'Ath Bilbao',
        'ATHLETIC CLUB': 'Ath Bilbao',
        'BETIS': 'Betis',
        'CELTA': 'Celta',
        'CELTA VIGO': 'Celta',
        'RAYO': 'Vallecano',
        'RAYO VALLECANO': 'Vallecano',
        'R.SOCIEDAD': 'Sociedad',
        'REAL SOCIEDAD': 'Sociedad',
        'SEVILLA': 'Sevilla',
        'MALLORCA': 'Mallorca',
        'OSASUNA': 'Osasuna',
        'ALAVES': 'Alaves',
        'GETAFE': 'Getafe',
        'LEGANES': 'Leganes',
        'LEGANÉS': 'Leganes',
        'VALLADOLID': 'Valladolid',
        'LAS PALMAS': 'Las Palmas',
        'VALENCIA': 'Valencia',
        'GIRONA': 'Girona',
        'ESPANYOL': 'Espanol',
        'ESPAÑOL': 'Espanol',
        # Segunda
        'R.OVIEDO': 'Oviedo',
        'REAL OVIEDO': 'Oviedo',
        'R.ZARAGOZA': 'Zaragoza',
        'REAL ZARAGOZA': 'Zaragoza',
        'RACING S.': 'Santander',
        'RACING SANTANDER': 'Santander',
        'S.GIJON': 'Sp Gijon',
        'SPORTING GIJON': 'Sp Gijon',
        'SPORTING': 'Sp Gijon',
        'D.CORUÑA': 'La Coruna',
        'DEPORTIVO LA CORUNA': 'La Coruna',
        'ALMERIA': 'Almeria',
        'CADIZ': 'Cadiz',
        'CÁDIZ': 'Cadiz',
        'GRANADA': 'Granada',
        'TENERIFE': 'Tenerife',
        'LEVANTE': 'Levante',
        'ELCHE': 'Elche',
        'EIBAR': 'Eibar',
        'MÁLAGA': 'Malaga',
        'MALAGA': 'Malaga',
        'ALBACETE': 'Albacete',
        'BURGOS': 'Burgos',
        'HUESCA': 'Huesca',
        'CASTELLON': 'Castellon',
        'CASTELLÓN': 'Castellon',
        'C. LEONESA': 'Cultural Leonesa',
        'C. LEONESA': 'Cultural Leonesa',
        'CULTURAL LEONESA': 'Cultural Leonesa',
        'MIRANDES': 'Mirandes',
        'MIRANDÉS': 'Mirandes',
        'CORDOBA': 'Cordoba',
        'CÓRDOBA': 'Cordoba',
        'CEUTA': 'Ceuta'
    }
    
    cleaned = []
    for m in matches_list:
        home, away = m.split(" - ")
        h = name_map.get(home.upper(), home.title())
        a = name_map.get(away.upper(), away.title())
        cleaned.append((h, a))
        
    return cleaned

if __name__ == "__main__":
    jornada = obtener_jornada_quiniela()
    for i, j in enumerate(jornada):
        print(f"{i+1}. {j[0]} vs {j[1]}")
