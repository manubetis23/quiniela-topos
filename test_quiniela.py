import requests
from bs4 import BeautifulSoup
import json
import urllib.request

try:
    url = "https://www.loteriasyapuestas.es/es/la-quiniela/escrutinios" 
    # Or eduardolosilla
    url2 = "https://www.eduardolosilla.es/quiniela/estimaciones"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url2, headers=headers)
    html = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(html, 'html.parser')
    
    matches = soup.find_all('div', class_='partido') # just a guess, I will print all text to find patterns
    texts = soup.get_text()
    
    lines = [line.strip() for line in texts.split('\n') if '-' in line and len(line.strip()) > 5]
    print("Posibles partidos encontrados en Eduardolosilla:")
    for l in lines[:30]:
        print(l)
        
except Exception as e:
    print("Error:", e)

