import streamlit as st
from modules.database import load_prospects


def render_analysis():
    df = load_prospects()
    st.subheader("Analyse commerciale")
    if df.empty:
        st.info("Aucune donnée.")
        return

    a1, a2 = st.columns(2)
    with a1:
        st.markdown("### Par température")
        st.bar_chart(df["temperature"].fillna("Non classé").value_counts())
    with a2:
        st.markdown("### Par statut")
        st.bar_chart(df["statut"].fillna("Non classé").value_counts())
    st.markdown("### Par source")
    st.bar_chart(df["source"].fillna("NC").value_counts().head(10))
    st.markdown("### Départements les plus actifs")
    st.bar_chart(df["departement"].fillna("NC").value_counts().head(15))
