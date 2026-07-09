import streamlit as st
from modules.database import load_prospects, save_messages
from modules.messages import build_linkedin_message, build_mail


def render_messages():
    df = load_prospects()
    st.subheader("Messages")
    if df.empty:
        st.info("Aucun prospect.")
        return

    ids = df["id"].astype(int).tolist()
    prospect_id = st.selectbox("Prospect", ids, format_func=lambda x: f"#{x} — {df.loc[df['id'] == x, 'cabinet'].iloc[0]}")
    variant = st.selectbox("Type de mail", ["agent", "court", "relance", "cabinet"])

    selected = df[df["id"] == int(prospect_id)]
    if selected.empty:
        st.warning("ID introuvable.")
        return

    row = selected.iloc[0].to_dict()
    mail = build_mail(row, variant)
    linkedin = build_linkedin_message(row)

    st.text_area("Mail", value=mail, height=360)
    st.text_area("LinkedIn", value=linkedin, height=180)

    if st.button("Sauvegarder les messages"):
        save_messages(int(prospect_id), mail, linkedin)
        st.success("Messages sauvegardés.")
