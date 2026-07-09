
import streamlit as st
from modules.database import load_prospects, save_messages
from modules.messages import build_linkedin_message, build_mail, build_subject

def render_messages():
    df = load_prospects()
    st.subheader("Messages")
    if df.empty:
        st.info("Aucun prospect.")
        return

    ids = df["id"].astype(int).tolist()
    prospect_id = st.selectbox(
        "Prospect",
        ids,
        format_func=lambda x: f"#{x} — {df.loc[df['id'] == x, 'cabinet'].iloc[0]}"
    )
    variant = st.selectbox("Type de mail", ["agent", "court", "relance", "cabinet"])

    selected = df[df["id"] == int(prospect_id)]
    if selected.empty:
        st.warning("ID introuvable.")
        return

    row = selected.iloc[0].to_dict()
    subject = build_subject(row)
    mail = build_mail(row, variant)
    linkedin = build_linkedin_message(row)

    st.markdown("### Objet du mail")
    st.code(subject, language=None)

    st.markdown("### Mail")
    st.text_area("Mail prêt à copier", value=mail, height=360)

    st.markdown("### LinkedIn")
    st.text_area("Message LinkedIn prêt à copier", value=linkedin, height=180)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Sauvegarder les messages"):
            save_messages(int(prospect_id), mail, linkedin)
            st.success("Messages sauvegardés.")
    with c2:
        email = row.get("email_public") or ""
        if email:
            st.link_button("Ouvrir Gmail", f"https://mail.google.com/mail/?view=cm&fs=1&to={email}&su={subject}")
        else:
            st.info("Ajoute un email dans le CRM pour ouvrir Gmail.")
    with c3:
        linkedin_url = row.get("linkedin") or ""
        if linkedin_url:
            st.link_button("Ouvrir LinkedIn", linkedin_url)
