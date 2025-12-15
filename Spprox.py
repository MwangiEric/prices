import requests
import streamlit as st

# Your proxy list URL (embeds auth token)
PROXY_LIST_URL = "https://proxy.webshare.io/api/v2/proxy/list/download/rsxcmuxgyewbbbbxbhuqsrwmwukqnnwuiprxodoh/-/any/username/direct/-/?plan_id=12426511"

st.title("Webshare Proxy List Test")

try:
    # Fetch the proxy list
    response = requests.get(PROXY_LIST_URL, timeout=15)
    response.raise_for_status()
    
    proxy_lines = response.text.strip().split("\n")
    
    if not proxy_lines or proxy_lines[0] == "":
        st.error("❌ Proxy list is empty.")
    else:
        st.success(f"✅ Retrieved {len(proxy_lines)} proxy entries.")
        
        first_proxy = proxy_lines[0]
        st.write("Sample proxy format (first entry):")
        st.code(first_proxy, language="text")
        
        # Optional: Validate format
        if "@" in first_proxy and ":" in first_proxy.split("@")[0]:
            st.write("✅ Format looks correct: `user:pass@host:port`")
        else:
            st.warning("⚠️ Unexpected format. Check Webshare settings.")
            
        # Optional: Test using the proxy
        if st.button("Test First Proxy Connectivity"):
            try:
                proxy_url = f"http://{first_proxy}"
                test_resp = requests.get(
                    "https://httpbin.org/ip",
                    proxies={"http": proxy_url, "https": proxy_url},
                    timeout=10
                )
                st.write("✅ Proxy is working. Response IP:")
                st.json(test_resp.json())
            except Exception as e:
                st.error(f"❌ Proxy test failed: {e}")

except requests.exceptions.RequestException as e:
    st.error(f"❌ Failed to fetch proxy list: {e}")
except Exception as e:
    st.error(f"Unexpected error: {e}")