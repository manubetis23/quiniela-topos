import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import sqlite3

def scrape_fbref_la_liga_stats():
    print("Iniciando scraping de FBref para La Liga 2024/2025...")
    
    # URL de la temporada actual de La Liga en FBref
    url = "https://fbref.com/en/comps/12/La-Liga-Stats"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con FBref: {e}")
        return None
        
    soup = BeautifulSoup(response.content, "html.parser")
    
    # 1. Extraer Estadísticas Estándar (Posesión, xG, xGA)
    # FBref tiene varias tablas. La principal de stats es 'stats_squads_standard_for'
    try:
        table_standard = soup.find("table", {"id": "stats_squads_standard_for"})
        df_standard = pd.read_html(str(table_standard))[0]
        
        # Limpiar el MultiIndex de columnas si existe
        if isinstance(df_standard.columns, pd.MultiIndex):
            df_standard.columns = df_standard.columns.droplevel()
            
        print("\nEstadísticas Estándar (Muestra):")
        print(df_standard[['Squad', 'Poss', 'xG', 'xGA']].head())
    except Exception as e:
        print(f"No se pudo parsear la tabla estándar: {e}")
        return None
        
    time.sleep(3) # Pausa amigable para evitar baneos
    
    # 2. Extraer Defensa (Tackles, Interceptions, Clearances - Opcional pero útil)
    try:
        table_defense = soup.find("table", {"id": "stats_squads_defense_for"})
        df_defense = pd.read_html(str(table_defense))[0]
        if isinstance(df_defense.columns, pd.MultiIndex):
            df_defense.columns = df_defense.columns.droplevel()
            
        print("\nEstadísticas Defensivas (Muestra):")
        print(df_defense[['Squad', 'TklW', 'Int', 'Clr']].head())
    except Exception as e:
        print(f"No se pudo parsear la tabla de defensa: {e}")
        df_defense = pd.DataFrame()
        
    time.sleep(3)
        
    # Consolidar datos
    print("\nConsolidando datos...")
    
    # Seleccionar columnas clave de Standard
    # Squad, Poss (Posesión), xG (Goles Esperados), xGA (Goles Esperados en Contra)
    cols_std = ['Squad', 'Poss', 'xG', 'xGA']
    df_final = df_standard[cols_std].copy()
    
    # Unir con Defensa si existe (TklW = Tackles Won, Int = Interceptions)
    if not df_defense.empty:
        cols_def = ['Squad', 'TklW', 'Int', 'Clr']
        df_final = pd.merge(df_final, df_defense[cols_def], on='Squad', how='left')
        
    # Limpiar y renombrar
    df_final = df_final.rename(columns={
        'Squad': 'Equipo',
        'Poss': 'avg_possession',
        'xG': 'avg_xG_season',
        'xGA': 'avg_xGA_season',
        'TklW': 'tackles_won_season',
        'Int': 'interceptions_season',
        'Clr': 'clearances_season'
    })
    
    # Eliminar fila de totales si existe
    df_final = df_final[df_final['Equipo'] != 'La Liga']
    
    print("\nDatos Finales Consolidados:")
    print(df_final.head())
    
    return df_final

def main():
    df_stats = scrape_fbref_la_liga_stats()
    
    if df_stats is not None and not df_stats.empty:
        csv_filename = "FBref_LaLiga_Stats.csv"
        df_stats.to_csv(csv_filename, index=False)
        print(f"\nDatos guardados en CSV: {csv_filename}")
        
        # Guardar en SQLite
        db_path = "quiniela_db.sqlite"
        try:
            conn = sqlite3.connect(db_path)
            df_stats.to_sql("equipos_stats_avanzadas_fbref", conn, if_exists="replace", index=False)
            conn.close()
            print(f"Datos guardados en la base de datos SQLite: {db_path} (Tabla: equipos_stats_avanzadas_fbref)")
        except Exception as e:
            print(f"Error escribiendo en SQLite: {e}")
    else:
        print("No se obtuvieron datos. Revisa los mensajes de error.")

if __name__ == "__main__":
    main()
