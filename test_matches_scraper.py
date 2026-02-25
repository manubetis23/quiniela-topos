import requests
from bs4 import BeautifulSoup
import re

def scrape_marca():
    url = "https://www.marca.com/apuestas-deportivas/quiniela.html"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Busca las tablas de partidos
    teams = soup.find_all('span', class_='equipo')
    for t in teams:
        print(t.text.strip())

def scrape_quinielista():
    url = "https://www.quinielista.es/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    # Buscar tabla
    matches = soup.find_all('td', class_='texto')
    for m in matches:
        if '-' in m.text:
            print(m.text.strip())

if __name__ == "__main__":
    print("Scraping Marca:")
    try: scrape_marca()
    except Exception as e: print(e)
    
    print("\nScraping Quinielista:")
    try: scrape_quinielista()
    except Exception as e: print(e)
