
from datetime import date
import re
import requests

from modules.config import get_env
from modules.database import save_prospects
from modules.scoring import (
    clean_company, detect_logiciel, detect_need_signal, google_search_url,
    linkedin_search_url, potential_ca, priority, sales_argument, score_offer,
    temperature, next_action, is_cabinet, is_recruiter
)

SOURCES = {
    "HelloWork": "site:hellowork.com gestionnaire paie cabinet comptable",
    "APEC": "site:apec.fr gestionnaire paie cabinet comptable",
    "Welcome": "site:welcometothejungle.com gestionnaire paie cabinet comptable",
    "Indeed": "site:fr.indeed.com gestionnaire paie cabinet comptable",
    "LinkedIn Jobs": "site:linkedin.com/jobs gestionnaire paie cabinet comptable",
    "Cabinets": "cabinet comptable recrute gestionnaire paie silae",
}

def tavily_search(query, max_results=8):
    key = get_env().get("tavily_key", "")
    if not key:
        return []
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": key,
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=25,
        )
        if r.status_code >= 400 or not r.text:
            return []
        return r.json().get("results", []) or []
    except Exception:
        return []

def guess_department(text):
    m = re.search(r"\b([0-9]{2})[0-9]{3}\b", text or "")
    if m:
        return m.group(1)
    m = re.search(r"\b(0[1-9]|[1-8][0-9]|9[0-5])\s*[-–]\s*", text or "")
    return m.group(1) if m else ""

def guess_city(text):
    cities = ["Lyon", "Villeurbanne", "Dardilly", "Nantes", "Rennes", "Angers", "Valence", "Grenoble", "Saint-Étienne", "Vannes", "La Roche-sur-Yon", "Dijon", "Paris"]
    low = (text or "").lower()
    for c in cities:
        if c.lower() in low:
            return c
    return ""

def guess_company(title, content):
    blob = f"{title} {content}"
    for p in [r"chez\s+([A-Z][A-Za-zÀ-ÿ0-9&' .-]{2,50})", r"cabinet\s+([A-Z][A-Za-zÀ-ÿ0-9&' .-]{2,50})"]:
        m = re.search(p, blob)
        if m:
            return clean_company(m.group(1).strip(" -|,.;"))
    parts = re.split(r"[-|–]", title or "")
    if parts and len(parts[0].strip()) > 2 and "gestionnaire" not in parts[0].lower():
        return clean_company(parts[0].strip())
    return "À identifier"

def result_to_prospect(item, source):
    title = item.get("title", "") or ""
    content = item.get("content", "") or ""
    url = item.get("url", "") or ""
    text = f"{title} {content} {url}"
    company = guess_company(title, content)
    city = guess_city(text)
    dep = guess_department(text)
    logiciel = detect_logiciel(text)
    signal = detect_need_signal(text)
    argument = sales_argument(signal, logiciel)
    cabinet_detecte = "Oui" if is_cabinet(text) else "À vérifier"
    recruteur = "Oui" if is_recruiter(company, text) else "Non"
    score = score_offer(text, "CDI", dep, company)
    temp = temperature(score, recruteur, cabinet_detecte, logiciel)
    return {
        "created_at": str(date.today()), "updated_at": str(date.today()),
        "source": source, "date_collecte": str(date.today()),
        "priorite": priority(score), "score": score, "temperature": temp,
        "potentiel_ca": potential_ca(score, logiciel, cabinet_detecte),
        "prochaine_action": next_action("À contacter", temp, ""),
        "cabinet": company, "cabinet_detecte": cabinet_detecte, "recruteur": recruteur,
        "ville": city, "departement": dep, "intitule_offre": title,
        "type_contrat": "", "logiciel": logiciel, "signal_besoin": signal,
        "argument_commercial": argument, "contact_public": "", "email_public": "",
        "telephone": "", "site_web": "", "linkedin": linkedin_search_url(company, city),
        "page_contact": "", "recherche_google": google_search_url(company, city),
        "lien_annonce": url, "statut": "À contacter", "date_contact": "",
        "relance_1": "", "relance_2": "", "dernier_message": "",
        "dernier_message_linkedin": "", "commentaires": f"Trouvé via moteur multi-sources ({source})",
    }

def run_multi_source_watch(departments, max_results=8):
    rows, errors = [], []
    dep_query = " ".join([f"département {d}" for d in departments if d])
    for source, base_query in SOURCES.items():
        q = f"{base_query} {dep_query} freelance marque blanche paie"
        try:
            results = tavily_search(q, max_results=max_results)
            rows.extend([result_to_prospect(item, source) for item in results])
        except Exception as e:
            errors.append(f"{source}: {e}")
    inserted, updated = save_prospects(rows)
    return inserted, updated, errors
