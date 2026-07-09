# LD Prospection Paie - V12.0

Version SaaS-ready pour Streamlit Community Cloud.

## Fonctionnalités
- Tableau de bord moderne
- Agent de veille France Travail
- Enrichissement Tavily / Google / DuckDuckGo
- CRM avec pipeline
- Générateur de mails et LinkedIn
- Actions du jour et relances
- Analyse commerciale
- Export Excel / CSV

## Lancer en local
```cmd
pip install -r requirements.txt
python -m streamlit run app.py
```

## Secrets Streamlit Cloud
```toml
FRANCE_TRAVAIL_CLIENT_ID = "..."
FRANCE_TRAVAIL_CLIENT_SECRET = "..."
TAVILY_API_KEY = "tvly-..."
GOOGLE_CUSTOM_SEARCH_API_KEY = ""
GOOGLE_CUSTOM_SEARCH_CX = ""
```
