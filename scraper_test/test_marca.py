import requests
from bs4 import BeautifulSoup
import re

url = "https://www.marca.com/apuestas-deportivas/quiniela/estimacion-porcentajes-jugados.html"
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(url, headers=headers)
print(res.status_code)
