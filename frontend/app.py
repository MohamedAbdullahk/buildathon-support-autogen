import os

import requests
import streamlit as st

# ============ Config ============

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SUPPORT_API = f"{BACKEND_URL}/api/v1/support"
HEALTH_API = f"{BACKEND_URL}/health"
REQUEST_TIMEOUT = 120  # seconds - agents can take time

st.set_page_config(page_title="AI Customer Support", page_icon="🤖", layout="wide")


# ============ API Helpers ============

@st.cache_data(ttl=30)
def get_backend_health():
    """Return backend health JSON, or None if the backend is down."""
    try:
        response = requests.get(HEALTH_API, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def call_support_api(query: str):
    """Call the backend. Returns (data, error_message)."""
    try:
        response = requests.post(
            SUPPORT_API, json={"query": query}, timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the backend. Is the API server running?"
    except requests.exceptions.Timeout:
        return None, "The request took too long. Please try again."

    if response.status_code == 422:
        return None, "Invalid request. Please check your query."

    if response.status_code != 200:
        try:
            detail = response.json().get("detail", "")
        except ValueError:
            detail = ""
        return None, detail or f"Backend error (HTTP {response.status_code})."

    return response.json(), None


# ============ Sidebar: System Status ============

with st.sidebar:
    st.header("⚙️ System Status")
    health = get_backend_health()
    if health:
        st.success("Backend: Online")
        st.caption(f"Model: {health.get('model', '-')}")
        if not health.get("keys_configured"):
            st.warning("API keys are not configured on the backend.")
    else:
        st.error("Backend: Offline")
        st.caption(f"Expected at: {BACKEND_URL}")


# ============ Main Page ============

st.title("🤖 Multi-Agent Customer Support")
st.caption("AutoGen: Assistant ➜ Web Search Assistant ➜ Entry Agent")

with st.form("query_form"):
    query = st.text_input(
        "Enter your query or task:",
        placeholder="e.g. How do I reset my password?",
        max_chars=500,
    )
    submitted = st.form_submit_button("Get Answers", type="primary")

if submitted:
    if not query.strip():
        st.warning("Please enter a query first.")
    else:
        with st.spinner("🤖 Agents are working... (Assistant ➜ Web Search ➜ Saving)"):
            data, error = call_support_api(query)
        st.session_state["result"] = data
        st.session_state["error"] = error

result = st.session_state.get("result")
error = st.session_state.get("error")

if error:
    st.error(f"❌ {error}")

elif result:
    if result["blocked"]:
        st.warning(f"🛡️ Blocked by guardrails: {result['block_reason']}")
    else:
        st.success(f"✅ Done in {result['duration_seconds']}s. Query and both answers saved.")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🧠 Assistant Answer")
            st.markdown(result["assistant_answer"] or "_No answer_")
        with col2:
            st.subheader("🌐 Web Search Answer")
            st.markdown(result["web_answer"] or "_No answer_")

        with st.expander("📝 See full agent conversation"):
            for item in result["trace"]:
                st.markdown(f"**{item['source']}** · `{item['type']}`")
                st.text(item["content"])
                st.divider()