import pandas as pd
import sqlite3
import os
import ssl

# Bypass SSL verify for macOS Python installers
ssl._create_default_https_context = ssl._create_unverified_context

def load_football_data(seasons=["2122", "2223", "2324", "2425", "2526"]):
    print(f"Recopilando datos históricos de La Liga (Primera y Segunda) para temporadas: {', '.join(seasons)}...")
    
    all_df_primera = []
    all_df_segunda = []
    
    for season in seasons:
        # URLs directas a los CSVs de football-data.co.uk (no bloquean)
        url_primera = f"https://www.football-data.co.uk/mmz4281/{season}/SP1.csv"
        url_segunda = f"https://www.football-data.co.uk/mmz4281/{season}/SP2.csv"
        
        try:
            df_p = pd.read_csv(url_primera)
            df_p['Competicion'] = 'La Liga'
            df_p['Season'] = season
            all_df_primera.append(df_p)
            print(f"La Liga ({season}): {len(df_p)} partidos cargados.")
        except Exception as e:
            print(f"Error cargando Primera temporada {season}: {e}")
            
        try:
            df_s = pd.read_csv(url_segunda)
            df_s['Competicion'] = 'La Liga 2'
            df_s['Season'] = season
            all_df_segunda.append(df_s)
            print(f"Segunda ({season}): {len(df_s)} partidos cargados.")
        except Exception as e:
            print(f"Error cargando Segunda temporada {season}: {e}")
            
    df_primera = pd.concat(all_df_primera, ignore_index=True) if all_df_primera else None
    df_segunda = pd.concat(all_df_segunda, ignore_index=True) if all_df_segunda else None
        
    return df_primera, df_segunda

def save_to_db(df_primera, df_segunda, db_path="quiniela_db.sqlite"):
    conn = sqlite3.connect(db_path)
    
    if df_primera is not None:
        df_primera.to_sql("partidos_historico", conn, if_exists="replace", index=False)
        df_primera.to_csv("LaLiga_Data.csv", index=False)
        
    if df_segunda is not None:
        df_segunda.to_sql("partidos_historico", conn, if_exists="append", index=False)
        df_segunda.to_csv("Segunda_Data.csv", index=False)
        
    print(f"Base de datos {db_path} y archivos CSV actualizados correctamente.")
    
    # Comprobación básica
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), Competicion FROM partidos_historico GROUP BY Competicion")
    res = cursor.fetchall()
    print("Resumen de partidos en DB:", res)
    conn.close()

if __name__ == "__main__":
    # Descargar las últimas 5 temporadas para entrenar el modelo
    df1, df2 = load_football_data()
    if df1 is not None or df2 is not None:
        save_to_db(df1, df2)
    else:
        print("No se pudieron cargar datos.")
