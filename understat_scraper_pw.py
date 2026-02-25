from playwright.sync_api import sync_playwright
import pandas as pd
from bs4 import BeautifulSoup
import sqlite3
import time

def scrape_understat_playwright():
    print("Iniciando scraping de Understat con Playwright (renderizado de JS)...")
    url = "https://understat.com/league/La_liga"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until="networkidle")
            # Esperar a que la tabla se cargue (contenedor principal)
            page.wait_for_selector("#league-chemp", timeout=15000)
            
            html_content = page.content()
        except Exception as e:
            print(f"Error cargando la página: {e}")
            browser.close()
            return None
            
        browser.close()

    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extraer los datos de la tabla visible
    try:
        table = soup.find(id="league-chemp").find("table")
        
        # Leemos el thead para las columnas
        headers = []
        for th in table.find('thead').find_all('th'):
            headers.append(th.text.strip())
            
        # Leemos el tbody para las filas
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            row_data = [td.text.strip() for td in tr.find_all('td')]
            rows.append(row_data)
            
        df = pd.DataFrame(rows, columns=headers)
        
        # Limpiar y preparar
        # Nos interesan 'Team', 'xG', 'xGA', 'xPTS'
        
        df_clean = pd.DataFrame({
            'Equipo': df['Team'],
            'avg_xG_season': pd.to_numeric(df['xG'].str.split('-').str[0].str.split('+').str[0]),
            'avg_xGA_season': pd.to_numeric(df['xGA'].str.split('-').str[0].str.split('+').str[0]),
            'avg_xpts_season': pd.to_numeric(df['xPTS'].str.split('-').str[0].str.split('+').str[0])
        })
        
        print("\nEstadísticas Avanzadas de Understat:")
        print(df_clean.head())
        return df_clean
        
    except Exception as e:
        print(f"Error parseando la tabla: {e}")
        return None

def main():
    df_stats = scrape_understat_playwright()
    
    if df_stats is not None and not df_stats.empty:
        csv_filename = "Understat_LaLiga_Stats.csv"
        df_stats.to_csv(csv_filename, index=False)
        print(f"\nDatos guardados en CSV: {csv_filename}")
        
        # Guardar en SQLite
        db_path = "quiniela_db.sqlite"
        try:
            conn = sqlite3.connect(db_path)
            df_stats.to_sql("equipos_stats_avanzadas", conn, if_exists="replace", index=False)
            conn.close()
            print(f"Datos estadísticos guardados en SQLite: {db_path} (Tabla principal: equipos_stats_avanzadas)")
        except Exception as e:
            print(f"Error escribiendo en SQLite: {e}")

if __name__ == "__main__":
    main()
