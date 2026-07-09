from datetime import date
import streamlit as st
from modules.database import load_prospects


def render_dashboard():
    df = load_prospects()
    st.subheader("Tableau de bord")
    if df.empty:
        st.info("Aucun prospect pour l’instant. Va dans l’onglet Agent et lance le moteur V15 multi-sources.")
        return

    today = str(date.today())
    enriched = int(((df["site_web"].fillna("") != "") | (df["email_public"].fillna("") != "") | (df["telephone"].fillna("") != "")).sum())
    relances = df[((df["relance_1"].fillna("") <= today) & (df["relance_1"].fillna("") != "")) | ((df["relance_2"].fillna("") <= today) & (df["relance_2"].fillna("") != ""))]

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Prospects", len(df))
    m2.metric("Nouveaux", int((df["created_at"] == today).sum()))
    m3.metric("Chauds", int((df["temperature"] == "Chaud").sum()))
    m4.metric("Enrichis", enriched)
    m5.metric("Relances", len(relances))
    m6.metric("RDV / réponses", int(df["statut"].isin(["Répondu", "RDV"]).sum()))

    st.markdown("### Priorités du jour")
    top = df[(df["statut"] == "À contacter") & (df["temperature"].isin(["Chaud", "Tiède"]))].head(30)
    st.dataframe(top[["id", "source", "temperature", "score", "prochaine_action", "signal_besoin", "cabinet", "ville", "logiciel", "contact_public", "email_public", "telephone", "site_web", "page_contact"]], use_container_width=True, hide_index=True)
