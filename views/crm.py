
import streamlit as st
from modules.database import load_prospects, update_prospect_details, quick_action
from modules.scoring import STATUSES

def _select_index(options, value, default=0):
    return options.index(value) if value in options else default

def render_crm():
    df = load_prospects()
    st.subheader("CRM")

    if df.empty:
        st.info("Aucun prospect à afficher. Lance d’abord une recherche dans l’onglet Agent.")
        return

    f1, f2, f3, f4 = st.columns(4)
    min_score = f1.slider("Score minimum", 0, 100, 50, 5)
    temp_filter = f2.multiselect("Température", ["Chaud", "Tiède", "Froid", "À vérifier"], default=[])
    statut_filter = f3.multiselect("Statut", STATUSES, default=[])
    only_enriched = f4.checkbox("Enrichis uniquement")

    view = df[df["score"] >= min_score].copy()
    if temp_filter:
        view = view[view["temperature"].isin(temp_filter)]
    if statut_filter:
        view = view[view["statut"].isin(statut_filter)]
    if only_enriched:
        view = view[(view["site_web"].fillna("") != "") | (view["email_public"].fillna("") != "") | (view["telephone"].fillna("") != "")]

    if view.empty:
        st.info("Aucun prospect ne correspond aux filtres.")
        return

    st.dataframe(
        view[["id", "source", "temperature", "priorite", "score", "potentiel_ca", "prochaine_action", "signal_besoin", "cabinet", "ville", "logiciel", "contact_public", "email_public", "telephone", "site_web", "page_contact", "linkedin", "statut", "relance_1", "relance_2", "commentaires"]],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.markdown("### Fiche prospect modifiable")

    ids = view["id"].astype(int).tolist()
    selected_id = st.selectbox(
        "Prospect à modifier",
        ids,
        format_func=lambda x: f"#{x} — {df.loc[df['id'] == x, 'cabinet'].iloc[0]}"
    )
    selected = df[df["id"] == int(selected_id)]
    if selected.empty:
        st.warning("Aucun prospect trouvé avec cet ID.")
        return

    prospect = selected.iloc[0].to_dict()

    st.markdown("#### Liens rapides")
    l1, l2, l3, l4 = st.columns(4)
    if prospect.get("site_web"):
        l1.link_button("Site web", prospect.get("site_web"))
    if prospect.get("page_contact"):
        l2.link_button("Page contact", prospect.get("page_contact"))
    if prospect.get("linkedin"):
        l3.link_button("LinkedIn", prospect.get("linkedin"))
    if prospect.get("recherche_google"):
        l4.link_button("Recherche Google", prospect.get("recherche_google"))

    st.markdown("#### Actions rapides")
    a1, a2, a3, a4, a5, a6 = st.columns(6)
    actions = [
        (a1, "Mail envoyé"),
        (a2, "LinkedIn envoyé"),
        (a3, "Appel effectué"),
        (a4, "Relance effectuée"),
        (a5, "RDV obtenu"),
        (a6, "Devenu client"),
    ]
    for col, label in actions:
        with col:
            if st.button(label):
                quick_action(int(selected_id), label)
                st.success(f"{label} enregistré.")

    col1, col2 = st.columns(2)
    with col1:
        cabinet = st.text_input("Cabinet", value=prospect.get("cabinet", ""))
        contact_public = st.text_input("Contact", value=prospect.get("contact_public", ""))
        email_public = st.text_input("Email", value=prospect.get("email_public", ""))
        telephone = st.text_input("Téléphone", value=prospect.get("telephone", ""))
        site_web = st.text_input("Site web", value=prospect.get("site_web", ""))
        linkedin = st.text_input("LinkedIn", value=prospect.get("linkedin", ""))

    with col2:
        statut = st.selectbox("Statut", STATUSES, index=_select_index(STATUSES, prospect.get("statut"), 0))
        priorite_options = ["Haute", "Moyenne", "Faible"]
        priorite = st.selectbox("Priorité", priorite_options, index=_select_index(priorite_options, prospect.get("priorite"), 1))
        temp_options = ["Chaud", "Tiède", "Froid", "À vérifier"]
        temperature = st.selectbox("Température", temp_options, index=_select_index(temp_options, prospect.get("temperature"), 1))
        ca_options = ["Fort", "Moyen", "Faible", "À vérifier"]
        potentiel_ca = st.selectbox("Potentiel CA", ca_options, index=_select_index(ca_options, prospect.get("potentiel_ca"), 3))
        date_contact = st.text_input("Date contact", value=prospect.get("date_contact", ""))
        relance_1 = st.text_input("Relance 1", value=prospect.get("relance_1", ""))
        relance_2 = st.text_input("Relance 2", value=prospect.get("relance_2", ""))

    page_contact = st.text_input("Page contact", value=prospect.get("page_contact", ""))
    commentaires = st.text_area("Notes / commentaires", value=prospect.get("commentaires", ""), height=160)

    if st.button("💾 Enregistrer la fiche prospect"):
        update_prospect_details(
            int(selected_id),
            {
                "cabinet": cabinet,
                "contact_public": contact_public,
                "email_public": email_public,
                "telephone": telephone,
                "site_web": site_web,
                "linkedin": linkedin,
                "page_contact": page_contact,
                "statut": statut,
                "priorite": priorite,
                "temperature": temperature,
                "potentiel_ca": potentiel_ca,
                "date_contact": date_contact,
                "relance_1": relance_1,
                "relance_2": relance_2,
                "commentaires": commentaires,
            },
        )
        st.success("Fiche prospect enregistrée.")
