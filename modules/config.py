
import os
from pathlib import Path

try:
    import streamlit as st
except Exception:
    st = None

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent

if load_dotenv:
    load_dotenv(dotenv_path=BASE_DIR / ".env")

def _get_secret(name, default=""):
    # 1) Streamlit Cloud secrets
    if st is not None:
        try:
            value = st.secrets.get(name, "")
            if value:
                return str(value).strip()
        except Exception:
            pass
    # 2) Local .env / environment
    return os.getenv(name, default).strip()

def get_env():
    return {
        "ft_client_id": _get_secret("FRANCE_TRAVAIL_CLIENT_ID"),
        "ft_client_secret": _get_secret("FRANCE_TRAVAIL_CLIENT_SECRET"),
        "google_key": _get_secret("GOOGLE_CUSTOM_SEARCH_API_KEY"),
        "google_cx": _get_secret("GOOGLE_CUSTOM_SEARCH_CX"),
        "tavily_key": _get_secret("TAVILY_API_KEY"),
    }

def env_status():
    env = get_env()
    return {
        "france_travail": bool(env["ft_client_id"] and env["ft_client_secret"]),
        "google": bool(env["google_key"] and env["google_cx"]),
        "tavily": bool(env["tavily_key"]),
    }
