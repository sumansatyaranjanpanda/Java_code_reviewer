# config/settings.py
import os
from pathlib import Path

# --- load local .env only if present (safe for dev)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    # local dev only; won't fail on deploy where .env isn't present
    from dotenv import load_dotenv
    load_dotenv(_env_path)

# --- helper: try Streamlit secrets if available
def _streamlit_secrets():
    try:
        import streamlit as st
        return st.secrets or {}
    except Exception:
        return {}

_stream_secrets = _streamlit_secrets()

def _get_secret(name, default=None):
    # priority: environment variable -> streamlit secrets -> default
    return os.getenv(name) or _stream_secrets.get(name) or default

# --- config values
GROQ_API_KEY = _get_secret("GROQ_API_KEY")
TAVILY_API_KEY = _get_secret("TAVILY_API_KEY")
OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
