
from datetime import date
import html
import re
import requests
from urllib.parse import unquote, urlparse, parse_qs

from modules.config import get_env
from modules.database import save_prospects
from modules.scoring import (
    clean_company, detect_logiciel, detect_need_signal, google_search_url,
    linkedin_search_url, potential_ca, priority, sales_argument, score_offer,
    temperature, next_action, is_cabinet, is_recruiter
)

# V16 : moteur multi-sources plus économique.
# Ordre de recherche : DuckDuckGo gratuit -> Google Custom Search -> Tavily en secours.

SOURCES = {
    "HelloWork": "site:hellowork.com",
    "Indeed": "site:fr.indeed.com",
    "APEC": "site:apec.fr",
    "Welcome": "site:welcometothejungle.com",
    "Meteojob": "site:meteojob.com",
    "Talent": "site:talent.com",
    "Sites cabinets": "cabinet comptable recrutement paie",
}

CITIES_BY_DEP = {
    "26": "Valence Romans Montelimar",
    "07": "Aubenas Privas Annonay",
    "38": "Grenoble Voiron Bourgoin",
    "69": "Lyon Villeurbanne Dardilly",
    "42": "Saint-Etienne Roanne",
    "44": "Nantes Saint-Herblain",
    "35": "Rennes Saint-Gregoire",
    "49": "Angers Cholet",
    "85": "La Roche-sur-Yon Les Sables Olonne",
}

def _is_useful_url(url):
    if not url:
        return False
    low = url.lower()
    blocked = ["google.", "bing.", "facebook.", "instagram.", "youtube.", "maps.google"]
    return low.startswith("http") and not any(b in low for b in blocked)

def duckduckgo_search(query, max_results=10):
    try:
        r = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        )
        if r.status_code >= 400 or not r.text:
            return []
        results = []
        for match in re.finditer(r'class="result__a" href="([^"]+)".*?>(.*?)</a>', r.text, re.S):
            href = html.unescape(match.group(1))
            title = re.sub("<.*?>", "", html.unescape(match.group(2))).strip()
            if "uddg=" in href:
                href = unquote(parse_qs(urlparse(href).query).get("uddg", [href])[0])
            if _is_useful_url(href):
                results.append({"title": title, "content": "", "url": href})
            if len(results) >= max_results:
                break
        return results
    except Exception:
        return []

def google_custom_search(query, max_results=10):
    env = get_env()
    if not env.get("google_key") or not env.get("google_cx"):
        return []
    try:
        r = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": env["google_key"], "cx": env["google_cx"], "q": query, "num": min(max_results, 10)},
            timeout=20,
        )
        if r.status_code >= 400 or not (r.text or "").strip():
            return []
        return [
            {"title": i.get("title", ""), "content": i.get("snippet", ""), "url": i.get("link", "")}
            for i in r.json().get("items", []) or []
            if _is_useful_url(i.get("link", ""))
        ]
    except Exception:
        return []

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
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=25,
        )
        if r.status_code >= 400 or not (r.text or "").strip():
            return []
        return r.json().get("results", []) or []
    except Exception:
        return []

def search_web(query, max_results=10):
    results = duckduckgo_search(query, max_results=max_results)
    if results:
        return results, "DuckDuckGo"
    results = google_custom_search(query, max_results=max_results)
    if results:
        return results, "Google"
    results = tavily_search(query, max_results=max_results)
    if results:
        return results, "Tavily"
    return [], "Aucune source"

def guess_department(text):
    text = text or ""
    m = re.search(r"\b([0-9]{2})[0-9]{3}\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b(0[1-9]|[1-8][0-9]|9[0-5])\s*[-–]\s*", text)
    if m:
        return m.group(1)
    low = text.lower()
    for dep, cities in CITIES_BY_DEP.items():
        for city in cities.split():
            if city.lower() in low:
                return dep
    return ""

def guess_city(text):
    cities = []
    for value in CITIES_BY_DEP.values():
        cities.extend(value.split())
    cities += ["Paris", "Marseille", "Bordeaux", "Toulouse", "Lille", "Dijon"]
    low = (text or "").lower()
    for c in cities:
        if c.lower() in low:
            return c
    return ""

def guess_company(title, content):
    blob = f"{title} {content}"
    patterns = [
        r"chez\s+([A-Z][A-Za-zÀ-ÿ0-9&' .-]{2,60})",
        r"recrute\s+([A-Z][A-Za-zÀ-ÿ0-9&' .-]{2,60})",
        r"cabinet\s+([A-Z][A-Za-zÀ-ÿ0-9&' .-]{2,60})",
    ]
    for p in patterns:
        m = re.search(p, blob)
        if m:
            return clean_company(m.group(1).strip(" -|,.;:"))

    parts = re.split(r"[-|–]", title or "")
    for part in parts:
        clean = part.strip()
        low = clean.lower()
        if len(clean) > 2 and "gestionnaire" not in low and "paie" not in low and "emploi" not in low:
            return clean_company(clean)
    return "À identifier"

def result_to_prospect(item, source):
    title = item.get("title", "") or ""
    content = item.get("content", "") or item.get("snippet", "") or ""
    url = item.get("url", "") or item.get("link", "") or ""
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
        "created_at": str(date.today()),
        "updated_at": str(date.today()),
        "source": source,
        "date_collecte": str(date.today()),
        "priorite": priority(score),
        "score": score,
        "temperature": temp,
        "potentiel_ca": potential_ca(score, logiciel, cabinet_detecte),
        "prochaine_action": next_action("À contacter", temp, ""),
        "cabinet": company,
        "cabinet_detecte": cabinet_detecte,
        "recruteur": recruteur,
        "ville": city,
        "departement": dep,
        "intitule_offre": title,
        "type_contrat": "",
        "logiciel": logiciel,
        "signal_besoin": signal,
        "argument_commercial": argument,
        "contact_public": "",
        "email_public": "",
        "telephone": "",
        "site_web": "",
        "linkedin": linkedin_search_url(company, city),
        "page_contact": "",
        "recherche_google": google_search_url(company, city),
        "lien_annonce": url,
        "statut": "À contacter",
        "date_contact": "",
        "relance_1": "",
        "relance_2": "",
        "dernier_message": "",
        "dernier_message_linkedin": "",
        "commentaires": f"Trouvé via moteur V16 ({source})",
    }

def build_queries(departments, keywords):
    queries = []
    for dep in departments:
        cities = CITIES_BY_DEP.get(dep, "")
        dep_part = f"{dep} {cities}".strip()
        for keyword in keywords:
            for source_name, source_filter in SOURCES.items():
                queries.append((source_name, f'{source_filter} "{keyword}" {dep_part}'))
    return queries

def run_multi_source_watch(departments, keywords, max_results=8):
    rows, errors = [], []
    seen_urls = set()

    queries = build_queries(departments, keywords)
    queries = queries[:80]  # limite de sécurité

    for source_name, query in queries:
        try:
            results, engine = search_web(query, max_results=max_results)
            for item in results:
                url = item.get("url") or item.get("link") or ""
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                rows.append(result_to_prospect(item, f"{source_name} / {engine}"))
        except Exception as e:
            errors.append(f"{source_name}: {e}")

    inserted, updated = save_prospects(rows)
    if not rows and not errors:
        errors.append("Aucun résultat exploitable trouvé. Essaye un seul département ou des requêtes plus larges : paie, silae, gestionnaire de paie.")
    return inserted, updated, errors
