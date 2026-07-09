
from datetime import date
import streamlit as st

from modules.config import env_status
from modules.database import init_db, load_prospects, load_actions, update_status, save_messages
from modules.enrichment import enrich_best_prospects
from modules.exports import build_excel_export
from modules.france_travail import run_watch
from modules.messages import build_linkedin_message, build_mail
from modules.multi_source import run_multi_source_watch
from modules.scoring import STATUSES

APP_VERSION = "V14.0"

st.set_page_config(
    page_title=f"LD Prospection Paie {APP_VERSION}",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown(
    """
<style>
.block-container {padding-top: 1.2rem;}
[data-testid="stMetricValue"] {font-size: 1.55rem;}
.ld-title {font-size: 2.2rem; font-weight: 800; color: #22313f; margin-bottom: 0;}
.ld-subtitle {color: #6b7280; margin-top: .2rem; margin-bottom: 1.1rem;}
.ld-badge {background:#f6f7f9; border:1px solid #e8e8e8; padding:.65rem .8rem; border-radius:12px;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<p class="ld-title">LD Prospection Paie - V14</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="ld-subtitle">Assistant commercial multi-sources pour détecter, qualifier, enrichir et suivre tes prospects paie.</p>',
    unsafe_allow_html=True,
)

status = env_status()
c1, c2, c3 = st.columns(3)
with c1:
    if status.get("france_travail"):
        st.success("✅ France Travail connecté")
    else:
        st.warning("⚠️ France Travail indisponible")
with c2:
    if status.get("tavily"):
        st.success("✅ Tavily connecté")
    else:
        st.warning("⚠️ Tavily non configuré")
with c3:
    if status.get("google"):
        st.success("✅ Google connecté")
    else:
        st.info("ℹ️ Google optionnel")

tabs = st.tabs(
    [
        "🏠 Dashboard",
        "🤖 Agent",
        "🗓️ Actions",
        "🏢 CRM",
        "✉️ Messages",
        "🌐 Enrichir",
        "📊 Analyse",
        "📤 Export",
        "🧾 Historique",
    ]
)

with tabs[0]:
    df = load_prospects()
    st.subheader("Tableau de bord")
    if df.empty:
        st.info("Aucun prospect pour l’instant. Va dans l’onglet Agent et lance le moteur V14 multi-sources.")
    else:
        today = str(date.today())
        enriched = int(
            (
                (df["site_web"].fillna("") != "")
                | (df["email_public"].fillna("") != "")
                | (df["telephone"].fillna("") != "")
            ).sum()
        )
        relances = df[
            ((df["relance_1"].fillna("") <= today) & (df["relance_1"].fillna("") != ""))
            | ((df["relance_2"].fillna("") <= today) & (df["relance_2"].fillna("") != ""))
        ]

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Prospects", len(df))
        m2.metric("Nouveaux", int((df["created_at"] == today).sum()))
        m3.metric("Chauds", int((df["temperature"] == "Chaud").sum()))
        m4.metric("Enrichis", enriched)
        m5.metric("Relances", len(relances))
        m6.metric("RDV / réponses", int(df["statut"].isin(["Répondu", "RDV"]).sum()))

        st.markdown("### Priorités du jour")
        top = df[(df["statut"] == "À contacter") & (df["temperature"].isin(["Chaud", "Tiède"]))].head(30)
        st.dataframe(
            top[
                [
                    "id",
                    "source",
                    "temperature",
                    "score",
                    "prochaine_action",
                    "signal_besoin",
                    "cabinet",
                    "ville",
                    "logiciel",
                    "email_public",
                    "telephone",
                    "site_web",
                    "page_contact",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

with tabs[1]:
    st.subheader("Agent de veille V14")

    st.markdown("### 🚀 Moteur multi-sources recommandé")
    st.caption("Utilise Tavily pour rechercher sur plusieurs sources publiques, sans dépendre uniquement de France Travail.")
    ms_departments = st.text_input("Départements", value="26,07,38,69,42,44,35,49,85", key="ms_departments")
    ms_keywords = st.text_area(
        "Requêtes multi-sources",
        value="gestionnaire paie cabinet comptable\ncollaborateur paie cabinet comptable\nresponsable paie cabinet comptable\nsilae paie cabinet comptable\ncabinet comptable recrute paie",
        height=120,
        key="ms_keywords",
    )
    ms_max = st.slider("Résultats max par source", 3, 20, 8, 1)
    enrich_after_ms = st.checkbox("Enrichir automatiquement les 10 meilleurs après la recherche", value=True)

    if st.button("🚀 Lancer le moteur multi-sources V14"):
        try:
            dep_list = [d.strip().zfill(2) for d in ms_departments.split(",") if d.strip().isdigit()]
            kw_list = [k.strip() for k in ms_keywords.splitlines() if k.strip()]
            with st.spinner("Recherche multi-sources en cours..."):
                inserted, updated, errors = run_multi_source_watch(dep_list, kw_list, ms_max)
                if enrich_after_ms:
                    enrich_best_prospects(10)
            if errors:
                st.warning(f"Recherche terminée avec {len(errors)} alerte(s). Nouveaux : {inserted}, déjà connus : {updated}.")
                with st.expander("Voir les alertes"):
                    for e in errors:
                        st.write(e)
            else:
                st.success(f"Recherche terminée : {inserted} nouveau(x), {updated} déjà connu(s).")
        except Exception as e:
            st.error(f"Erreur multi-sources : {e}")

    st.divider()
    st.markdown("### France Travail — optionnel")
    st.caption("À utiliser uniquement si l’API France Travail répond correctement. Le moteur multi-sources reste prioritaire.")
    departments = st.text_input("Départements France Travail", value="69", key="ft_departments")
    keywords = st.text_area(
        "Requêtes France Travail",
        value="gestionnaire paie\ngestionnaire de paie\ncollaborateur paie",
        height=100,
        key="ft_keywords",
    )
    max_results = st.slider("Résultats max France Travail par requête et département", 10, 80, 30, 10)

    if st.button("Lancer France Travail"):
        try:
            kw_list = [k.strip() for k in keywords.splitlines() if k.strip()]
            dep_list = [d.strip().zfill(2) for d in departments.split(",") if d.strip().isdigit()]
            with st.spinner("Recherche France Travail en cours..."):
                inserted, updated, errors = run_watch(kw_list, dep_list, max_results)
            if errors:
                st.warning(f"France Travail terminé avec {len(errors)} alerte(s). Nouveaux : {inserted}, déjà connus : {updated}.")
                with st.expander("Voir les alertes France Travail"):
                    for e in errors:
                        st.write(e)
            else:
                st.success(f"France Travail terminé : {inserted} nouveau(x), {updated} déjà connu(s).")
        except Exception as e:
            st.error(f"Erreur France Travail : {e}")

with tabs[2]:
    df = load_prospects()
    st.subheader("Actions du jour")
    if df.empty:
        st.info("Aucun prospect.")
    else:
        today = str(date.today())
        to_contact = df[(df["statut"] == "À contacter") & (df["temperature"].isin(["Chaud", "Tiède"]))].head(50)
        relances = df[
            ((df["relance_1"].fillna("") <= today) & (df["relance_1"].fillna("") != "") & (df["statut"].isin(["Contacté", "Relance 1"])))
            | ((df["relance_2"].fillna("") <= today) & (df["relance_2"].fillna("") != "") & (df["statut"].isin(["Contacté", "Relance 1", "Relance 2"])))
        ]

        st.markdown("### À contacter")
        st.dataframe(
            to_contact[["id", "temperature", "score", "prochaine_action", "cabinet", "ville", "logiciel", "email_public", "telephone", "site_web", "linkedin"]],
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("### Relances")
        st.dataframe(
            relances[["id", "cabinet", "ville", "statut", "date_contact", "relance_1", "relance_2", "email_public", "telephone"]],
            use_container_width=True,
            hide_index=True,
        )

with tabs[3]:
    df = load_prospects()
    st.subheader("CRM")
    if df.empty:
        st.info("Aucun prospect.")
    else:
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
            view = view[
                (view["site_web"].fillna("") != "")
                | (view["email_public"].fillna("") != "")
                | (view["telephone"].fillna("") != "")
            ]

        st.dataframe(
            view[
                [
                    "id",
                    "source",
                    "temperature",
                    "priorite",
                    "score",
                    "potentiel_ca",
                    "prochaine_action",
                    "signal_besoin",
                    "cabinet",
                    "ville",
                    "logiciel",
                    "email_public",
                    "telephone",
                    "site_web",
                    "page_contact",
                    "linkedin",
                    "statut",
                    "relance_1",
                    "relance_2",
                    "commentaires",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Mise à jour rapide")
        default_id = int(view.iloc[0]["id"]) if not view.empty else 1
        prospect_id = st.number_input("ID prospect", min_value=1, value=default_id)
        new_status = st.selectbox("Nouveau statut", STATUSES)
        comment = st.text_input("Commentaire")
        if st.button("Mettre à jour le prospect"):
            update_status(int(prospect_id), new_status, comment)
            st.success("Prospect mis à jour.")

with tabs[4]:
    df = load_prospects()
    st.subheader("Messages")
    if df.empty:
        st.info("Aucun prospect.")
    else:
        prospect_id = st.number_input("ID prospect pour message", min_value=1, value=int(df.iloc[0]["id"]))
        variant = st.selectbox("Type de mail", ["agent", "court", "relance", "cabinet"])
        selected = df[df["id"] == prospect_id]
        if selected.empty:
            st.warning("ID introuvable.")
        else:
            row = selected.iloc[0].to_dict()
            mail = build_mail(row, variant)
            linkedin = build_linkedin_message(row)
            st.text_area("Mail", value=mail, height=360)
            st.text_area("LinkedIn", value=linkedin, height=180)
            if st.button("Sauvegarder les messages"):
                save_messages(int(prospect_id), mail, linkedin)
                st.success("Messages sauvegardés.")

with tabs[5]:
    st.subheader("Enrichissement web")
    st.write("Utilise Tavily si configuré, sinon Google Custom Search, sinon DuckDuckGo en secours.")
    limit = st.slider("Nombre de prospects à enrichir", 1, 50, 10)
    if st.button("Enrichir les meilleurs prospects"):
        try:
            with st.spinner("Enrichissement en cours..."):
                count = enrich_best_prospects(limit)
            st.success(f"{count} prospect(s) traité(s).")
        except Exception as e:
            st.error(f"Erreur enrichissement : {e}")

with tabs[6]:
    df = load_prospects()
    st.subheader("Analyse commerciale")
    if df.empty:
        st.info("Aucune donnée.")
    else:
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

with tabs[7]:
    df = load_prospects()
    st.subheader("Export")
    if df.empty:
        st.info("Aucun prospect à exporter.")
    else:
        excel_data = build_excel_export(df)
        st.download_button(
            "Télécharger Excel V14",
            excel_data,
            f"ld_prospection_paie_v14_{date.today()}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        csv = df.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button("Télécharger CSV", csv, f"ld_prospection_paie_v14_{date.today()}.csv", "text/csv")

with tabs[8]:
    actions = load_actions()
    st.subheader("Historique")
    if actions.empty:
        st.info("Aucune action.")
    else:
        st.dataframe(actions, use_container_width=True, hide_index=True)
