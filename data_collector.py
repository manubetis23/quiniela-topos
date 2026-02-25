import pandas as pd
import sqlite3
import os
import ssl

# Bypass SSL verify for macOS Python installers
ssl._create_default_https_context = ssl._create_unverified_context

def load_football_data(season="2526"):
    print("Recopilando datos de La Liga (Primera y Segunda)...")
    
    # URLs directas a los CSVs de football-data.co.uk (no bloquean)
    url_primera = f"https://www.football-data.co.uk/mmz4281/{season}/SP1.csv"
    url_segunda = f"https://www.football-data.co.uk/mmz4281/{season}/SP2.csv"
    
    try:
        df_primera = pd.read_csv(url_primera)
        df_primera['Competicion'] = 'La Liga'
        print(f"La Liga ({season}): {len(df_primera)} partidos cargados.")
    except Exception as e:
        print(f"Error cargando Primera: {e}")
        df_primera = None
        
    try:
        df_segunda = pd.read_csv(url_segunda)
        df_segunda['Competicion'] = 'La Liga 2'
        print(f"Segunda ({season}): {len(df_segunda)} partidos cargados.")
    except Exception as e:
        print(f"Error cargando Segunda: {e}")
        df_segunda = None
        
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
    df1, df2 = load_football_data("2526")
    if df1 is not None or df2 is not None:
        save_to_db(df1, df2)
    else:
        print("No se pudieron cargar datos.")
