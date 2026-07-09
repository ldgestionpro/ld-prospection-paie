import streamlit as st
from modules.enrichment import enrich_best_prospects


def render_enrich():
    st.subheader("Enrichissement web")
    st.write("Utilise Tavily si configuré, sinon Google Custom Search, sinon DuckDuckGo en secours.")
    limit = st.slider("Nombre de prospects à enrichir", 1, 50, 10)

    if st.button("Enrichir les meilleurs prospects"):
        try:
            with st.spinner("Enrichissement en cours..."):
                count = enrich_best_prospects(limit)
            st.success(f"{count} prospect(s) traité(s).")
        except Exception as e:
            st.error(f"Erreur enrichissement : {e}")
