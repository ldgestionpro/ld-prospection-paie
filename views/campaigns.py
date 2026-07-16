import streamlit as st

from modules.database import load_campaigns, close_campaign


def render_campaigns():
    st.subheader("Historique des campagnes")

    campaigns = load_campaigns()

    if campaigns.empty:
        st.info("Aucune campagne enregistrée pour l’instant.")
        return

    st.dataframe(
        campaigns[
            [
                "id",
                "created_at",
                "source",
                "departments",
                "keywords",
                "new_count",
                "known_count",
                "status",
            ]
        ],
        width="stretch",
        hide_index=True,
    )

    campaign_ids = campaigns["id"].astype(int).tolist()
    selected_id = st.selectbox(
        "Campagne à clôturer",
        campaign_ids,
        format_func=lambda value: f"Campagne #{value}",
    )

    if st.button("Clôturer la campagne"):
        close_campaign(int(selected_id))
        st.success(f"Campagne #{selected_id} clôturée.")
