import streamlit as st
from modules.enrichment import enrich_best_prospects
from modules.france_travail import run_watch
from modules.multi_source import run_multi_source_watch


def render_agent():
    st.subheader("Agent de veille V16")
    st.markdown("### 🚀 Moteur multi-sources recommandé")
    st.caption("Utilise Tavily pour rechercher sur plusieurs sources publiques, sans dépendre uniquement de France Travail.")
    ms_departments = st.text_input("Départements", value="26,07,38,69,42,44,35,49,85", key="ms_departments")
    ms_keywords = st.text_area(
        "Requêtes multi-sources",
        value="gestionnaire de paie\ngestionnaire paie\ncollaborateur paie\nresponsable paie\nsilae paie\ncabinet comptable recrute paie",
        height=140,
        key="ms_keywords",
    )
    ms_max = st.slider("Résultats max par source", 3, 20, 8, 1)
    enrich_after_ms = st.checkbox("Enrichir automatiquement les 10 meilleurs après la recherche", value=True)

    if st.button("🚀 Lancer le moteur multi-sources V16"):
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
    keywords = st.text_area("Requêtes France Travail", value="gestionnaire paie\ngestionnaire de paie\ncollaborateur paie", height=100, key="ft_keywords")
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
