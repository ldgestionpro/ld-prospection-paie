from datetime import date
import streamlit as st
from modules.database import load_prospects
from modules.exports import build_excel_export


def render_export():
    df = load_prospects()
    st.subheader("Export")
    if df.empty:
        st.info("Aucun prospect à exporter.")
        return

    excel_data = build_excel_export(df)
    st.download_button("Télécharger Excel V15", excel_data, f"ld_prospection_paie_v15_{date.today()}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    csv = df.to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button("Télécharger CSV", csv, f"ld_prospection_paie_v15_{date.today()}.csv", "text/csv")
