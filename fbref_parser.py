import pandas as pd
from bs4 import BeautifulSoup
import sqlite3

def parse_fbref_html(html_file_path):
    print(f"Leyendo HTML desde {html_file_path}...")
    
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 1. Extraer Estadísticas Estándar (Posesión, xG, xGA)
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
        
    # Consolidar datos
    print("\nConsolidando datos...")
    
    # Seleccionar columnas clave de Standard
    cols_std = ['Squad', 'Poss', 'xG', 'xGA']
    df_final = df_standard[cols_std].copy()
        
    # Limpiar y renombrar
    df_final = df_final.rename(columns={
        'Squad': 'Equipo',
        'Poss': 'avg_possession',
        'xG': 'avg_xG_season',
        'xGA': 'avg_xGA_season',
    })
    
    # Eliminar fila de totales si existe
    df_final = df_final[df_final['Equipo'] != 'vs Opponent']
    
    print("\nDatos Finales Consolidados:")
    print(df_final.head())
    
    return df_final

def main():
    df_stats = parse_fbref_html("fbref_laliga_source.html")
    
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
