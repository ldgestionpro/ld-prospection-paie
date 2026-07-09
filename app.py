import streamlit as st

from modules.config import env_status
from modules.database import init_db
from views.dashboard import render_dashboard
from views.agent import render_agent
from views.actions import render_actions
from views.crm import render_crm
from views.messages_view import render_messages
from views.enrich import render_enrich
from views.analysis import render_analysis
from views.export_view import render_export
from views.history import render_history

APP_VERSION = "V16.0"

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
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<p class="ld-title">LD Prospection Paie - V16</p>', unsafe_allow_html=True)
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

tabs = st.tabs([
    "🏠 Tableau de bord", "🤖 Agent", "🗓️ Actions", "🏢 CRM", "✉️ Messages",
    "🌐 Enrichir", "📊 Analyse", "📤 Export", "🧾 Historique",
])

with tabs[0]:
    render_dashboard()
with tabs[1]:
    render_agent()
with tabs[2]:
    render_actions()
with tabs[3]:
    render_crm()
with tabs[4]:
    render_messages()
with tabs[5]:
    render_enrich()
with tabs[6]:
    render_analysis()
with tabs[7]:
    render_export()
with tabs[8]:
    render_history()
