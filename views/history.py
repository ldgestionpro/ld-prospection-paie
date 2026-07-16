import streamlit as st
from modules.database import load_actions


def render_history():
    actions = load_actions()
    st.subheader("Historique")
    if actions.empty:
        st.info("Aucune action.")
    else:
        st.dataframe(actions, width="stretch", hide_index=True)
