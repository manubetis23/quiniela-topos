import requests
from bs4 import BeautifulSoup
import re
import json

url = "https://www.quinielista.es/escrutinio"
headers = {'User-Agent': 'Mozilla/5.0'}

res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'lxml')
print(f"Len html: {len(res.text)}")
# In quinielista, look for "Porcentajes apostados" or similar
for div in soup.find_all('div', class_=re.compile(r'porcentajes')):
    print(div.text)

