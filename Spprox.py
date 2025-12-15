# gsm_user_proxy.py
import streamlit as st
import requests
import random
import time
import json
from bs4 import BeautifulSoup

# --------------------------------------------------
#  HARD-CODED 2025 PROXY LIST  (HTTPS/SOCKS5 + High-Anon)
# --------------------------------------------------
PROXY_POOL = [
    "https://180.183.157.159:8080",      # Thailand
    "https://46.4.96.137:1080",          # Germany  (SOCKS5)
    "https://47.91.88.100:1080",         # Germany  (SOCKS5)
    "https://45.77.56.114:30205",        # UK       (SOCKS5)
    "https://82.196.11.105:1080",        # NL       (SOCKS5)
    "https://51.254.69.243:3128",        # France
    "https://178.62.193.19:1080",        # NL       (SOCKS5)
    "https://188.226.141.127:1080",      # NL       (SOCKS5)
    "https://217.23.6.40:1080",          # NL       (SOCKS5)
    "https://185.153.198.226:32498",     # Moldova  (SOCKS5)
    "https://81.171.24.199:3128",        # NL
    "https://5.189.224.84:10000",        # RU       (SOCKS5)
    "https://108.61.175.73:1802",        # UK       (SOCKS5)
    "https://176.31.200.104:3128",       # France
    "https://83.77.118.53:17171",        # CH
    "https://173.192.21.89:80",          # US
    "https://163.172.182.164:3128",      # France
    "https://163.172.168.124:3128",      # France
    "https://164.68.105.235:3128",       # US
    "https://5.199.171.227:3128",        # Lithuania
    "https://93.171.164.25:8080",        # RU
    "https://212.112.97.27:3128",        # Kyrgyzstan
    "https://51.68.207.81:80",           # UK
    "https://91.211.245.176:8080",       # Lithuania
    "https://84.201.254.47:3128",        # RU
    "https://95.156.82.35:3128",         # RU
    "https://185.118.141.254:8080",      # Turkey
    "https://164.68.98.169:9300",        # Germany  (SOCKS5)
    "https://217.113.122.142:3128",      # RU
    "https://188.100.212.208:21129",     # Germany
]

# --------------------------------------------------
#  UI TOGGLE  (checkbox)
# --------------------------------------------------
use_proxy = st.sidebar.checkbox("Use proxy (rotate every request)", value=True)

def get_proxy():
    if not use_proxy:
        return {}
    px = random.choice(PROXY_POOL)
    return {"https": px, "http": px}      # both mappings just in case

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
                st.warning("429 hit – cooling 30 s")
                time.sleep(30); continue
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            st.error(f"Request error: {e}")
            time.sleep(random.uniform(2, 4))
    return None

# --------------------------------------------------
#  GSMARENA LOGIC
# --------------------------------------------------
GSM = "https://www.gsmarena.com/"

@st.cache_data(ttl=3600, show_spinner=False)
def gsm_search_suggestions(query: str):
    soup = get_soup(f"{GSM}res.php3?sSearch={query}")
    if not soup:
        return []
    return [(a.get_text(strip=True), a["href"]) for a in soup.select(".makers a")]

def get_specs(rel_url: str):
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
#  STREAMLIT UI
# --------------------------------------------------
st.set_page_config(page_title="GSMArena Proxy-Toggle Search", layout="centered")
st.title("📱 GSMArena Search")
st.markdown("Toggle proxy use in the left sidebar.")

query = st.text_input("Search phone:", placeholder="iPhone 16 Pro").strip()
if query:
    with st.spinner("Fetching suggestions…"):
        hits = gsm_search_suggestions(query)
    if not hits:
        st.error("No results found.")
        st.stop()

    chosen_name, chosen_url = st.selectbox(
        "Pick the exact model:",
        options=hits,
        format_func=lambda x: x[0]
    )

    if st.button("Load full specs"):
        with st.spinner("Pulling specs…"):
            specs = get_specs(chosen_url)
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
