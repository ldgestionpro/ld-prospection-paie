from datetime import date
import streamlit as st
from modules.database import load_prospects


def render_actions():
    df = load_prospects()
    st.subheader("Actions du jour")
    if df.empty:
        st.info("Aucun prospect.")
        return

    today = str(date.today())
    to_contact = df[(df["statut"] == "À contacter") & (df["temperature"].isin(["Chaud", "Tiède"]))].head(50)
    relances = df[((df["relance_1"].fillna("") <= today) & (df["relance_1"].fillna("") != "") & (df["statut"].isin(["Contacté", "Relance 1"]))) | ((df["relance_2"].fillna("") <= today) & (df["relance_2"].fillna("") != "") & (df["statut"].isin(["Contacté", "Relance 1", "Relance 2"])))]

    st.markdown("### À contacter")
    st.dataframe(to_contact[["id", "temperature", "score", "prochaine_action", "cabinet", "ville", "logiciel", "contact_public", "email_public", "telephone", "site_web", "linkedin"]], width="stretch", hide_index=True)

    st.markdown("### Relances")
    st.dataframe(relances[["id", "cabinet", "ville", "statut", "date_contact", "relance_1", "relance_2", "email_public", "telephone"]], width="stretch", hide_index=True)
