import pandas as pd
import sqlite3
from playwright.sync_api import sync_playwright
import time

def scrape_standings(url, competition_name):
    print(f"Extrayendo datos de {competition_name} con Playwright...")
    try:
        with sync_playwright() as p:
            # Iniciamos navegador invisible
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Navegamos a la web
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3) # damos margen adicional a las tablas
            
            # Extraemos el HTML de la página ya renderizada
            html = page.content()
            browser.close()
            
            # Buscamos la tabla con Pandas
            tables = pd.read_html(html)
            
            standings = tables[0]
            standings['Competicion'] = competition_name
            return standings
            
    except Exception as e:
        print(f"Error extrayendo datos de {url}: {e}")
        return None

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    return conn

def main():
    url_primera = "https://fbref.com/en/comps/12/La-Liga-Stats"
    url_segunda = "https://fbref.com/en/comps/17/Segunda-Division-Stats"
    
    df_primera = scrape_standings(url_primera, "La Liga")
    
    # Hacemos una pausa para que no bloqueen por rate-limit
    print("Pausa de 5 segundos antes de buscar Segunda División...")
    time.sleep(5)
    
    df_segunda = scrape_standings(url_segunda, "La Liga 2")
    
    db_path = "quiniela_db.sqlite"
    conn = init_db(db_path)
    
    if df_primera is not None:
        df_primera.to_sql("clasificacion_actual", conn, if_exists="replace", index=False)
        print("Clasificacion de Primera División guardada con éxito en SQLite.")
        
    if df_segunda is not None:
        df_segunda.to_sql("clasificacion_actual", conn, if_exists="append", index=False)
        print("Clasificacion de Segunda División guardada con éxito en SQLite.")
        
    conn.close()
    print(f"Proceso finalizado. Puedes encontrar tu base de datos en: {db_path}")

if __name__ == "__main__":
    main()
