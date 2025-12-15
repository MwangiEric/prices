# gsm_pa_proxy.py
import streamlit as st
import requests
import random
import time
import json
from bs4 import BeautifulSoup

# --------------------------------------------------
#  FRESH PROXY LOADER  (auto-fetched, 5-min cache)
# --------------------------------------------------
@st.cache_data(ttl=300)
def load_fresh_proxies():
    urls = [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http,socks5&timeout=10000&country=all",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    ]
    proxies = []
    for url in urls:
        try:
            text = requests.get(url, timeout=10).text
            for line in text.splitlines():
                line = line.strip()
                if ":" in line and len(line.split(":")) == 2:
                    proxies.append(f"https://{line}")
        except Exception as e:
            st.write("Proxy source failed:", e)
    return list(set(proxies))

# --------------------------------------------------
#  PROXY TOGGLE  (default OFF)
# --------------------------------------------------
use_proxy = st.sidebar.checkbox("Use proxy (rotate every request)", value=False)
PROXY_POOL = load_fresh_proxies()

def get_proxy():
    if not use_proxy or not PROXY_POOL:
        return {}
    px = random.choice(PROXY_POOL)
    return {"https": px, "http": px}

# --------------------------------------------------
#  REQUEST SESSION
# --------------------------------------------------
session = requests.Session()
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

def random_headers():
    session.headers.update({"User-Agent": random.choice(UA_POOL),
                            "Accept-Language": "en-US,en;q=0.9"})

def get_soup(url):
    for attempt in range(3):
        try:
            random_headers()
            r = session.get(url, proxies=get_proxy(), timeout=12)
            if r.status_code == 429:
                st.warning("429 – cooling 30 s")
                time.sleep(30); continue
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            st.error(f"Request error: {e}")
            time.sleep(random.uniform(2, 4))
    return None

# --------------------------------------------------
#  GSMARENA PARSER
# --------------------------------------------------
GSM = "https://www.gsmarena.com/"

@st.cache_data(ttl=3600, show_spinner=False)
def gsm_search_suggestions(query: str):
    soup = get_soup(f"{GSM}res.php3?sSearch={query}")
    if not soup:
        return []
    return [(a.get_text(strip=True), a["href"]) for a in soup.select(".makers a")]

def gsm_specs(rel_url: str):
    soup = get_soup(GSM + rel_url)
    if not soup:
        return {}
    specs = {}
    for tr in soup.select("table.specs tr"):
        tds = tr.find_all("td")
        if len(tds) == 2:
            key, val = [td.get_text(" ", strip=True) for td in tds]
            specs[key] = val
    return specs

# --------------------------------------------------
#  PHONEARENA PARSER
# --------------------------------------------------
PA = "https://www.phonearena.com/"

@st.cache_data(ttl=3600, show_spinner=False)
def pa_search_suggestions(query: str):
    url = f"{PA}search?k={query}"
    soup = get_soup(url)
    if not soup:
        return []
    return [(a.get_text(strip=True), a["href"]) for a in soup.select('.search-item-result a[href*="/phones/"]')]

def pa_specs(rel_url: str):
    soup = get_soup(PA + rel_url)
    if not soup:
        return {}
    specs = {}
    for row in soup.select(".phone-specs-table tr"):
        tds = row.find_all("td")
        if len(tds) == 2:
            key, val = [td.get_text(" ", strip=True) for td in tds]
            specs[key] = val
    return specs

# --------------------------------------------------
#  STREAMLIT UI
# --------------------------------------------------
st.set_page_config(page_title="Phone Scraper", layout="centered")
st.title("📱 Phone Scraper (GSMArena + PhoneArena)")
site = st.sidebar.radio("Choose site:", ("GSMArena", "PhoneArena"))

query = st.text_input("Search phone:", placeholder="iPhone 16 Pro").strip()
if query:
    with st.spinner(f"Fetching {site} suggestions…"):
        hits = gsm_search_suggestions(query) if site == "GSMArena" else pa_search_suggestions(query)
    if not hits:
        st.error("No results found.")
        st.stop()

    chosen_name, chosen_url = st.selectbox(
        "Pick the exact model:",
        options=hits,
        format_func=lambda x: x[0]
    )

    if st.button("Load full specs"):
        with st.spinner(f"Pulling specs from {site}…"):
            specs = gsm_specs(chosen_url) if site == "GSMArena" else pa_specs(chosen_url)
        if specs:
            st.success(f"Specs for **{chosen_name}**")
            st.table(specs)
            st.download_button(
                label="Download JSON",
                data=json.dumps(specs, indent=2, ensure_ascii=False),
                file_name=f"{chosen_name.replace(' ', '_')}.json",
                mime="application/json"
            )
        else:
            st.error("Could not retrieve specs.")
