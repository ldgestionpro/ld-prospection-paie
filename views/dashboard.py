from datetime import date
import streamlit as st
from modules.database import load_prospects, load_campaigns


def render_dashboard():
    df = load_prospects()
    st.subheader("Tableau de bord")
    if df.empty:
        st.info("Aucun prospect pour l’instant. Va dans l’onglet Agent et lance le moteur V18 multi-sources.")
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

    campaigns = load_campaigns()

    if not campaigns.empty:
        last = campaigns.iloc[0]
        st.markdown("### Dernière recherche")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Campagne", f"#{int(last['id'])}")
        c2.metric("Départements", last.get("departments", ""))
        c3.metric("Nouveaux", int(last.get("new_count", 0) or 0))
        c4.metric("Déjà connus", int(last.get("known_count", 0) or 0))

    st.markdown("### Priorités du jour")
    top = df[(df["statut"] == "À contacter") & (df["temperature"].isin(["Chaud", "Tiède"]))].head(30)
    st.dataframe(top[["id", "campaign_id", "source", "temperature", "score", "prochaine_action", "signal_besoin", "cabinet", "ville", "logiciel", "contact_public", "email_public", "telephone", "site_web", "page_contact"]], width="stretch", hide_index=True)
