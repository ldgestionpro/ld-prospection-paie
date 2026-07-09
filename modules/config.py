
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

def get_env():
    return {
        "ft_client_id": os.getenv("FRANCE_TRAVAIL_CLIENT_ID", "").strip(),
        "ft_client_secret": os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET", "").strip(),
        "google_key": os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY", "").strip(),
        "google_cx": os.getenv("GOOGLE_CUSTOM_SEARCH_CX", "").strip(),
        "tavily_key": os.getenv("TAVILY_API_KEY", "").strip(),
    }

def env_status():
    env = get_env()
    return {
        "france_travail": bool(env["ft_client_id"] and env["ft_client_secret"]),
        "google": bool(env["google_key"] and env["google_cx"]),
        "tavily": bool(env["tavily_key"]),
    }
