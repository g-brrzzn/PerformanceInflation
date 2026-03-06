import requests
import re
import time
import json
import os
from config import RAWG_API_KEY

CACHE_FILE = 'cache_rawg.json'

def extract_gpus_from_text(requirements_text):
    if not requirements_text: return []
    pattern = r'(?:GTX|RTX|RX|R9|HD)\s*\d{3,4}(?:\s*(?:Ti|SUPER|XT))?'
    matches = re.findall(pattern, requirements_text, re.IGNORECASE)
    return [re.sub(r'\s+', ' ', match).strip().upper() for match in matches]

def fetch_rawg_requirements(year, games_limit):
    cache_data = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
            
    year_str = str(year)
    if year_str in cache_data and len(cache_data[year_str]) > 0:
        print(f"\n[RAWG] Requirements for {year} loaded instantly from cache.")
        return cache_data[year_str]

    print(f"\n[RAWG] Fetching {games_limit} AAA games from {year} online...")
    list_url = f"https://api.rawg.io/api/games?dates={year}-01-01,{year}-12-31&ordering=-rating_count&platforms=4&page_size=20&key={RAWG_API_KEY}"
    
    try:
        resp = requests.get(list_url, timeout=10)
        resp.raise_for_status()
        list_data = resp.json()
    except Exception as e:
        print(f"Error in RAWG API (List): {e}")
        return []

    found_gpus = []
    processed_games = 0

    for game_summary in list_data.get('results', []):
        if processed_games >= games_limit: break
            
        game_name = game_summary.get('name')
        game_id = game_summary.get('id')
        
        detail_url = f"https://api.rawg.io/api/games/{game_id}?key={RAWG_API_KEY}"
        
        try:
            detail_resp = requests.get(detail_url, timeout=10)
            game_detail = detail_resp.json()
            time.sleep(0.2) 
        except Exception:
            print(f"  [!] Failed to fetch details for '{game_name}'")
            continue
            
        pc_found = False
        for platform in game_detail.get('platforms', []):
            if platform.get('platform', {}).get('slug') == 'pc':
                pc_found = True
                requirements = platform.get('requirements_en') or platform.get('requirements')
                
                if not requirements: break

                if isinstance(requirements, dict):
                    req_text = requirements.get('recommended') or requirements.get('minimum')
                    
                    if req_text:
                        gpus = extract_gpus_from_text(req_text)
                        if gpus:
                            print(f"  [V] '{game_name}': {', '.join(gpus)}")
                            found_gpus.extend(gpus)
                            processed_games += 1
                break
                
    cache_data[year_str] = found_gpus
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=4)

    return found_gpus