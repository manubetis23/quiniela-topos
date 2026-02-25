import requests
import json
import pandas as pd
import sqlite3
import re
from bs4 import BeautifulSoup

def scrape_understat_laliga():
    print("Iniciando scraping de Understat para La Liga...")
    url = "https://understat.com/league/La_liga"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error al conectar con Understat: {e}")
        return None
        
    # Understat inyecta los datos en una variable global de JS llamada 'teamsData'
    # Extraemos ese JSON usando expresiones regulares
    html_content = response.text
    try:
        data_match = re.search(r"var teamsData\s*=\s*JSON\.parse\('([^']+)'\);", html_content)
        if not data_match:
            print("No se encontró la variable JSON 'teamsData' en el HTML. Understat podría haber cambiado la estructura.")
            return None
            
        json_data_str = data_match.group(1)
        # El JSON_parse en javascript evalua unicode escapes. En python encode y decode lo arreglan
        json_data_str = json_data_str.encode('utf-8').decode('unicode_escape')
        teams_data = json.loads(json_data_str)
        
    except Exception as e:
        print(f"Error extrayendo JSON: {e}")
        return None

    # teams_data es un dict con IDs como llaves
    rows = []
    for team_id, team_info in teams_data.items():
        team_title = team_info['title']
        history = team_info['history']
        
        # history es una lista de todos los partidos jugados hasta la fecha.
        # Sumamos los stats acumulados
        matches_played = len(history)
        total_xG = sum(h['xG'] for h in history)
        total_xGA = sum(h['xGA'] for h in history)
        total_xpts = sum(h['xpts'] for h in history)
        
        # Calcular promedios por partido
        avg_xG = total_xG / matches_played if matches_played > 0 else 0
        avg_xGA = total_xGA / matches_played if matches_played > 0 else 0
        avg_xpts = total_xpts / matches_played if matches_played > 0 else 0
        
        # Ultimos 5 partidos (forma)
        recent_matches = history[-5:]
        avg_xG_recent = sum(h['xG'] for h in recent_matches) / len(recent_matches) if recent_matches else 0
        avg_xGA_recent = sum(h['xGA'] for h in recent_matches) / len(recent_matches) if recent_matches else 0

        rows.append({
            'Equipo': team_title,
            'partidos_jugados': matches_played,
            'avg_xG_season': round(avg_xG, 2),
            'avg_xGA_season': round(avg_xGA, 2),
            'avg_xpts_season': round(avg_xpts, 2),
            'avg_xG_recent': round(avg_xG_recent, 2),
            'avg_xGA_recent': round(avg_xGA_recent, 2)
        })
        
    df = pd.DataFrame(rows)
    print("\nEstadísticas Avanzadas de Understat (Primeras filas):")
    print(df.head())
    return df

def main():
    df_stats = scrape_understat_laliga()
    
    if df_stats is not None and not df_stats.empty:
        csv_filename = "Understat_LaLiga_Stats.csv"
        df_stats.to_csv(csv_filename, index=False)
        print(f"\nDatos guardados en CSV: {csv_filename}")
        
        # Guardar en SQLite
        db_path = "quiniela_db.sqlite"
        try:
            conn = sqlite3.connect(db_path)
            # Como FBref falló, usaremos understat
            df_stats.to_sql("equipos_stats_avanzadas", conn, if_exists="replace", index=False)
            conn.close()
            print(f"Datos estadísticos guardados en SQLite: {db_path} (Tabla principal: equipos_stats_avanzadas)")
        except Exception as e:
            print(f"Error escribiendo en SQLite: {e}")

if __name__ == "__main__":
    main()
