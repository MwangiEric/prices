# bridge_dash.py
import streamlit as st
import requests
import feedparser
import pandas as pd
from datetime import datetime

# --------------------------------------------------
#  CONFIG – your own bridge
# --------------------------------------------------
BRIDGE = "https://rss-57uz.onrender.com"

# --------------------------------------------------
#  PROXY TOGGLE  (re-uses your old helper)
# --------------------------------------------------
use_proxy = st.sidebar.checkbox("Use proxy", value=False)
PROXY_POOL = []   # fill or leave empty

def get_proxy():
    if not use_proxy or not PROXY_POOL:
        return {}
    return {"https": random.choice(PROXY_POOL), "http": random.choice(PROXY_POOL)}

# --------------------------------------------------
#  FEED FETCHER
# --------------------------------------------------
def fetch_feed(endpoint: str):
    url = BRIDGE + endpoint
    r = requests.get(url, proxies=get_proxy(), timeout=15)
    r.raise_for_status()
    return feedparser.parse(r.text)

# --------------------------------------------------
#  STREAMLIT UI
# --------------------------------------------------
st.set_page_config(page_title="Bridge Dashboard", layout="wide")
st.title("📡 RSS-Bridge Dashboard – phones, news, prices")

# ---------- 1.  PHONE / GADGET SPECS  ----------
with st.expander("📱 Latest phone specs (GSMArena)", expanded=True):
    d = fetch_feed("/?action=display&bridge=GSMarenaBridge&action=phones&format=Json")
    if d.entries:
        df = pd.DataFrame([{"Date": datetime.strptime(e.published, "%Y-%m-%d %H:%M:%S"),
                            "Phone": e.title,
                            "Link": e.link} for e in d.entries])
        st.dataframe(df, use_container_width=True)
        for e in d.entries[:5]:
            st.markdown(f"- [{e.title}]({e.link})")
    else:
        st.info("No entries – bridge may be empty.")

# ---------- 2.  TECH NEWS  ----------
cols = st.columns(2)
with cols[0]:
    with st.expander("🌐 Engadget", expanded=True):
        d = fetch_feed("/?action=display&bridge=EngadgetBridge&format=Json")
        for e in d.entries[:5]:
            st.markdown(f"- [{e.title}]({e.link})  – {e.published[:-9]}")
with cols[1]:
    with st.expander("🔬 Ars Technica", expanded=True):
        d = fetch_feed("/?action=display&bridge=ArsTechnicaBridge&format=Json")
        for e in d.entries[:5]:
            st.markdown(f"- [{e.title}]({e.link})  – {e.published[:-9]}")

# ---------- 3.  PRICE WATCHING  ----------
st.subheader("💰 Price feeds")
keyword = st.text_input("Amazon search keyword:", value="Samsung Galaxy S25 FE")
if keyword:
    d = fetch_feed(f"/?action=display&bridge=AmazonBridge&q={keyword.replace(' ', '+')}&format=Json")
    if d.entries:
        for e in d.entries[:10]:
            st.markdown(f"- [{e.title}]({e.link})  – {e.get('amazon_price', 'N/A')}")
    else:
        st.info("No Amazon results – try another keyword.")

# ---------- 4.  Idealo (EU price comparison) ----------
gtin = st.text_input("Idealo GTIN / EAN (13 digits):", placeholder="8806095212349")
if gtin and len(gtin) == 13:
    d = fetch_feed(f"/?action=display&bridge=IdealoBridge&gtin={gtin}&format=Json")
    if d.entries:
        for e in d.entries:
            st.markdown(f"- [{e.title}]({e.link})  – **{e.get('idealo_price', '?')} €**")
    else:
        st.info("No Idealo offers – GTIN may be unknown.")
