import requests
from bs4 import BeautifulSoup
import json
import os

CACHE_FILE = 'cache_passmark.json'

def fetch_passmark_scores():
    if os.path.exists(CACHE_FILE):
        print("[PassMark] Loading database from local cache...")
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)

    print("[PassMark] Downloading full database from internet...")
    url = "https://www.videocardbenchmark.net/gpu_list.php"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    scores = {}
    for row in soup.find('table', id='cputable').find('tbody').find_all('tr'):
        columns = row.find_all('td')
        if len(columns) >= 2:
            name = columns[0].find('a').text.strip()
            try:
                scores[name] = int(columns[1].text.strip().replace(',', ''))
            except ValueError:
                continue
                
    with open(CACHE_FILE, 'w') as f:
        json.dump(scores, f, indent=4)
        
    return scores

def find_score(search_name, scores_dict):
    if not scores_dict or not search_name: return None
    search_upper = search_name.upper()
    
    for official_name, score in scores_dict.items():
        official_upper = official_name.upper()
        if search_upper in official_upper:
            if "MOBILE" not in search_upper and ("MOBILE" in official_upper or " M" in official_upper): continue
            if "LAPTOP" not in search_upper and "LAPTOP" in official_upper: continue
            if "TI" not in search_upper and "TI" in official_upper.split(): continue
            if "SUPER" not in search_upper and "SUPER" in official_upper.split(): continue
            if "XT" not in search_upper and "XT" in official_upper.split(): continue
            return score
    return None