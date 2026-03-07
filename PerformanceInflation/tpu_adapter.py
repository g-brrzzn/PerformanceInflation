import requests
import json
import os
import re
import time
import random
from typing import Optional

GPU_DATA_CACHE = 'cache_gpu_data.json'

FALLBACK_DATA = {
    'GTX 660': {'year': 2012, 'msrp': 229},
    'GTX 760': {'year': 2013, 'msrp': 249},
    'GTX 960': {'year': 2015, 'msrp': 199},
    'GTX 1060': {'year': 2016, 'msrp': 249},
    'RTX 2060': {'year': 2019, 'msrp': 349},
    'RTX 3060': {'year': 2021, 'msrp': 329},
    'RTX 4060': {'year': 2023, 'msrp': 299},
    'RTX 5060': {'year': 2025, 'msrp': 299},
    'GTX 670': {'year': 2012, 'msrp': 399},
    'GTX 770': {'year': 2013, 'msrp': 399},
    'GTX 970': {'year': 2014, 'msrp': 329},
    'GTX 1070': {'year': 2016, 'msrp': 379},
    'RTX 2070': {'year': 2018, 'msrp': 499},
    'RTX 3070': {'year': 2020, 'msrp': 499},
    'RTX 4070': {'year': 2023, 'msrp': 599},
    'RTX 5070': {'year': 2025, 'msrp': 549},
    'GTX 680': {'year': 2012, 'msrp': 499},
    'GTX 780': {'year': 2013, 'msrp': 649},
    'GTX 980': {'year': 2014, 'msrp': 549},
    'GTX 1080': {'year': 2016, 'msrp': 599},
    'RTX 2080': {'year': 2018, 'msrp': 699},
    'RTX 3080': {'year': 2020, 'msrp': 699},
    'RTX 4080': {'year': 2022, 'msrp': 1199},
    'RTX 5080': {'year': 2025, 'msrp': 999},
    'GTX 690': {'year': 2012, 'msrp': 999},
    'GTX 790': {'year': 2014, 'msrp': 999},
    'GTX 990': {'year': 2015, 'msrp': 999},
    'GTX 1090': {'year': 2016, 'msrp': 1199},
    'RTX 2090': {'year': 2018, 'msrp': 2499},
    'RTX 3090': {'year': 2020, 'msrp': 1499},
    'RTX 4090': {'year': 2022, 'msrp': 1599},
    'RTX 5090': {'year': 2025, 'msrp': 1999},
    'HD 7850': {'year': 2012, 'msrp': 249},
    'R9 270X': {'year': 2013, 'msrp': 199},
    'R9 380': {'year': 2015, 'msrp': 199},
    'RX 480': {'year': 2016, 'msrp': 239},
    'RX 5600 XT': {'year': 2020, 'msrp': 279},
    'RX 6600': {'year': 2021, 'msrp': 329},
    'RX 7600': {'year': 2023, 'msrp': 269},
    'RX 8600': {'year': 2025, 'msrp': 299},
    'HD 7950': {'year': 2012, 'msrp': 449},
    'R9 280X': {'year': 2013, 'msrp': 299},
    'R9 390': {'year': 2015, 'msrp': 329},
    'RX Vega 56': {'year': 2017, 'msrp': 399},
    'RX 5700 XT': {'year': 2019, 'msrp': 399},
    'RX 6700 XT': {'year': 2021, 'msrp': 479},
    'RX 7700 XT': {'year': 2023, 'msrp': 449},
    'RX 8700 XT': {'year': 2025, 'msrp': 449},
    'HD 7970': {'year': 2012, 'msrp': 549},
    'R9 290X': {'year': 2013, 'msrp': 549},
    'R9 Fury': {'year': 2015, 'msrp': 549},
    'RX Vega 64': {'year': 2017, 'msrp': 499},
    'RX 5800 XT': {'year': 2020, 'msrp': 549},
    'RX 6800 XT': {'year': 2020, 'msrp': 649},
    'RX 7800 XT': {'year': 2023, 'msrp': 499},
    'RX 8800 XT': {'year': 2025, 'msrp': 499},
    'HD 7990': {'year': 2013, 'msrp': 999},
    'R9 295X2': {'year': 2014, 'msrp': 1499},
    'R9 Fury X': {'year': 2015, 'msrp': 649},
    'Radeon VII': {'year': 2019, 'msrp': 699},
    'RX 5900 XTX': {'year': 2020, 'msrp': 999},
    'RX 6900 XTX': {'year': 2020, 'msrp': 999},
    'RX 7900 XTX': {'year': 2022, 'msrp': 999},
    'RX 8900 XTX': {'year': 2025, 'msrp': 999}
}

try:
    import cloudscraper
    HAVE_CLOUDSCRAPER = True
except Exception:
    HAVE_CLOUDSCRAPER = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; performance-inflation-bot/1.0; +https://github.com/)",
    "Accept": "application/json, text/html;q=0.9,*/*;q=0.8"
}

def _load_cache():
    if os.path.exists(GPU_DATA_CACHE):
        try:
            with open(GPU_DATA_CACHE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_cache(cache):
    try:
        with open(GPU_DATA_CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def _safe_int_from_str(s):
    try:
        s = str(s)
        m = re.search(r'([0-9]{1,4}(?:[.,][0-9]{3})*(?:[.,]\d+)?)', s)
        if not m:
            return None
        v = m.group(1).replace('.', '').replace(',', '.')
        return int(round(float(v)))
    except Exception:
        return None

def _valid_year(y: int) -> bool:
    if not isinstance(y, int):
        return False
    return 1999 <= y <= 2026

def _valid_price(p: int) -> bool:
    if not isinstance(p, int):
        return False
    return 50 <= p <= 3000

def _normalize_queries(gpu_name: str):
    q = gpu_name.strip()
    variants = [q]
    if q.lower().startswith('gtx') or q.lower().startswith('rtx'):
        variants.append('GeForce ' + q)
    if q.lower().startswith('geforce '):
        variants.append(q.replace('GeForce ', '').strip())
    variants += [v.replace(' ', '_') for v in list(variants)]
    variants += [v.lower().replace(' ', '-') for v in list(variants)]
    seen = set()
    out = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out

WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"

def _wikidata_search_first(q: str) -> Optional[str]:
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": q,
        "type": "item",
        "limit": 5
    }
    r = requests.get(WIKIDATA_SEARCH_URL, params=params, headers=HEADERS, timeout=12)
    r.raise_for_status()
    j = r.json()
    for ent in j.get("search", []):
        label = ent.get("label", "")
        qid = ent.get("id")
        if q.lower().replace('_', ' ') in label.lower():
            return qid
    if j.get("search"):
        return j["search"][0].get("id")
    return None

def _parse_wikidata_price(claim) -> Optional[int]:
    try:
        snak = claim.get('mainsnak', {})
        dv = snak.get('datavalue', {})
        if not dv:
            return None
        v = dv.get('value')
        if isinstance(v, dict) and 'amount' in v:
            s = str(v['amount']).lstrip('+')
            return _safe_int_from_str(s)
        if isinstance(v, (str, int, float)):
            return _safe_int_from_str(v)
        s = json.dumps(v)
        return _safe_int_from_str(s)
    except Exception:
        return None

def _parse_wikidata_date(claim) -> Optional[int]:
    try:
        snak = claim.get('mainsnak', {})
        dv = snak.get('datavalue', {})
        if not dv:
            return None
        v = dv.get('value')
        if isinstance(v, dict) and 'time' in v:
            t = v['time']
            m = re.search(r'([+-]?\d{4})', t)
            if m:
                y = int(m.group(1))
                return y
        return _safe_int_from_str(str(v))
    except Exception:
        return None

def _wikidata_get_price_and_year(qid: str) -> Optional[dict]:
    url = WIKIDATA_ENTITY_URL.format(qid)
    r = requests.get(url, headers=HEADERS, timeout=12)
    r.raise_for_status()
    j = r.json()
    ent = j.get("entities", {}).get(qid, {})
    claims = ent.get("claims", {})
    result = {"year": None, "msrp": None, "provenance": {"source": "wikidata", "qid": qid, "url": url}}
    if "P2284" in claims:
        for c in claims["P2284"]:
            p = _parse_wikidata_price(c)
            if p and _valid_price(p):
                result["msrp"] = p
                break
    for pcode in ("P577", "P571", "P580", "P585"):
        if pcode in claims and result["year"] is None:
            for c in claims[pcode]:
                y = _parse_wikidata_date(c)
                if y and _valid_year(y):
                    result["year"] = y
                    break
        if result["year"]:
            break
    if result["year"] or result["msrp"]:
        return result
    return None

WIKI_API = "https://en.wikipedia.org/w/api.php"

def _wikipedia_infobox_price_and_year(title: str) -> Optional[dict]:
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "format": "json",
        "titles": title,
        "formatversion": 2
    }
    r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=12)
    if r.status_code != 200:
        return None
    j = r.json()
    pages = j.get("query", {}).get("pages", [])
    if not pages:
        return None
    page = pages[0]
    if "missing" in page:
        return None
    revs = page.get("revisions")
    content = revs[0].get("content", "") if revs else ""
    msrp = None
    year = None
    for line in content.splitlines():
        m_price = re.match(r'^\|\s*(?:price|launch ?price|base ?price|msrp|release ?price)\s*=\s*(.+)$', line.strip(), flags=re.IGNORECASE)
        if m_price and not msrp:
            val = m_price.group(1)
            val = re.sub(r'\{\{.*?\}\}', '', val)
            val = re.sub(r'\[\[|\]\]', '', val)
            v = _safe_int_from_str(val)
            if v and _valid_price(v):
                msrp = v
        m_date = re.match(r'^\|\s*(?:date|released|release ?date|launch ?date)\s*=\s*(.+)$', line.strip(), flags=re.IGNORECASE)
        if m_date and not year:
            val = m_date.group(1)
            y = _safe_int_from_str(val)
            if isinstance(y, int) and _valid_year(y):
                year = y
    if msrp or year:
        return {"msrp": msrp, "year": year, "provenance": {"source": "wikipedia", "title": title, "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}" }}
    return None

def _try_techpowerup_search_and_parse(gpu_name: str) -> Optional[dict]:
    if not HAVE_CLOUDSCRAPER:
        return None
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        base_search = "https://www.techpowerup.com/gpu-specs/"
        params = {"ajaxsrch": gpu_name.replace(" ", "+")}
        r = scraper.get(base_search, params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        html = r.text
        m = re.search(r'(/gpu-specs/[^\"]+)', html)
        href = None
        if not m:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                if '/gpu-specs/' in a['href']:
                    txt = (a.get_text() or '').lower()
                    if gpu_name.lower().split()[0] in txt or gpu_name.lower().replace(' ', '-') in a['href']:
                        href = a['href']
                        break
            if not href:
                for a in soup.find_all('a', href=True):
                    if '/gpu-specs/' in a['href']:
                        href = a['href']
                        break
            if not href:
                return None
            slug = href
        else:
            slug = m.group(1)
        url = "https://www.techpowerup.com" + slug
        r2 = scraper.get(url, headers=HEADERS, timeout=15)
        if r2.status_code != 200:
            return None
        from bs4 import BeautifulSoup
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        data = {"msrp": None, "year": None, "provenance": {"source": "techpowerup", "url": url}}
        for dl in soup2.find_all('dl'):
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')
            for dt, dd in zip(dts, dds):
                k = (dt.get_text() or '').strip().lower()
                v = (dd.get_text() or '').strip()
                if any(x in k for x in ('release date', 'launch date', 'released')):
                    m_year = re.search(r'([12]\d{3})', v)
                    if m_year:
                        y = int(m_year.group(1))
                        if _valid_year(y):
                            data['year'] = y
                if any(x in k for x in ('release price', 'launch price', 'msrp', 'price')):
                    p = _safe_int_from_str(v)
                    if p and _valid_price(p):
                        data['msrp'] = p
        if data['year'] or data['msrp']:
            return data
    except Exception:
        return None
    return None

def fetch_gpu_data(gpu_name: str) -> Optional[dict]:
    gpu_name = gpu_name.strip()
    cache = _load_cache()

    if gpu_name in cache:
        entry = cache[gpu_name]
        year_ok = entry.get('year') is not None and _valid_year(entry.get('year'))
        msrp_ok = entry.get('msrp') is not None and _valid_price(entry.get('msrp'))
        if year_ok and msrp_ok:
            print(f"[TechPowerUp Adapter] (cache) returning valid data for '{gpu_name}': {entry.get('year')} / ${entry.get('msrp')}")
            return entry
        else:
            print(f"[TechPowerUp Adapter] (cache) invalid/incomplete entry for '{gpu_name}', forcing re-fetch.")
            try:
                del cache[gpu_name]
                _save_cache(cache)
            except Exception:
                pass

    print(f"[TechPowerUp Adapter] Fetching data for '{gpu_name}' (Wikidata -> Wikipedia -> TechPowerUp)...")
    queries = _normalize_queries(gpu_name)

    partial = {"year": None, "msrp": None, "provenance": None}

    for q in queries:
        try:
            qid = _wikidata_search_first(q)
            if qid:
                res = _wikidata_get_price_and_year(qid)
                if res:
                    if res.get('msrp') and res.get('year'):
                        cache[gpu_name] = res
                        _save_cache(cache)
                        print(f"  [OK:Wikidata] Found via QID={qid}: {res.get('year')} / ${res.get('msrp')}")
                        return res
                    if res.get('year'):
                        partial['year'] = res.get('year')
                        partial['provenance'] = res.get('provenance')
                    if res.get('msrp'):
                        partial['msrp'] = res.get('msrp')
                        partial['provenance'] = res.get('provenance')
        except Exception as e:
            print(f"  [WARN] Wikidata error for '{q}': {e}")
            time.sleep(0.2 + random.random()*0.2)

    for q in queries:
        try:
            title = q.replace('-', ' ').replace('_', ' ')
            res_wp = _wikipedia_infobox_price_and_year(title)
            if res_wp:
                if res_wp.get('msrp') and _valid_price(res_wp.get('msrp')):
                    partial['msrp'] = res_wp.get('msrp')
                    partial['provenance'] = res_wp.get('provenance')
                if res_wp.get('year') and _valid_year(res_wp.get('year')):
                    partial['year'] = res_wp.get('year')
                    partial['provenance'] = res_wp.get('provenance')
                if partial.get('msrp') and partial.get('year'):
                    cache[gpu_name] = partial
                    _save_cache(cache)
                    print(f"  [OK:Wikipedia] Found via title='{title}': {partial.get('year')} / ${partial.get('msrp')}")
                    return partial
        except Exception as e:
            print(f"  [WARN] Wikipedia error for '{q}': {e}")
            time.sleep(0.2 + random.random()*0.2)

    try:
        res_tpu = _try_techpowerup_search_and_parse(gpu_name)
        if res_tpu:
            if res_tpu.get('msrp') and _valid_price(res_tpu.get('msrp')):
                partial['msrp'] = res_tpu.get('msrp')
                partial['provenance'] = res_tpu.get('provenance')
            if res_tpu.get('year') and _valid_year(res_tpu.get('year')):
                partial['year'] = res_tpu.get('year')
                partial['provenance'] = res_tpu.get('provenance')
            if partial.get('msrp') and partial.get('year'):
                cache[gpu_name] = partial
                _save_cache(cache)
                print(f"  [OK:TechPowerUp] Found: {partial.get('year')} / ${partial.get('msrp')}")
                return partial
    except Exception as e:
        print(f"  [WARN] TechPowerUp attempt failed: {e}")

    if partial.get('msrp') and partial.get('year'):
        cache[gpu_name] = partial
        _save_cache(cache)
        print(f"  [OK:combined sources] {partial.get('year')} / ${partial.get('msrp')}")
        return partial

    if gpu_name in FALLBACK_DATA:
        fb = FALLBACK_DATA[gpu_name].copy()
        fb['provenance'] = {'source': 'hardcoded_fallback'}
        cache[gpu_name] = fb
        _save_cache(cache)
        print(f"  [Fallback] Using internal safety database for {gpu_name}.")
        return fb

    cache[gpu_name] = {"year": None, "msrp": None, "provenance": {"source": "none"}}
    _save_cache(cache)
    print(f"  [Fail] Could not obtain data for '{gpu_name}'.")
    return None

if __name__ == "__main__":
    tests = ["GTX 960", "GTX 1060", "RTX 3060", "RTX 4060"]
    for t in tests:
        print("TEST:", t, fetch_gpu_data(t))