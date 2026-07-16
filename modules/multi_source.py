
from datetime import date
import html
import re
import requests
from urllib.parse import unquote, urlparse, parse_qs

from modules.config import get_env
from modules.database import (
    save_prospects,
    create_campaign,
    update_campaign_counts,
)
from modules.scoring import (
    clean_company,
    detect_logiciel,
    detect_need_signal,
    google_search_url,
    linkedin_search_url,
    potential_ca,
    priority,
    sales_argument,
    score_offer,
    temperature,
    next_action,
    is_cabinet,
    is_recruiter,
)

# V19 : requêtes plus larges, filtrage après récupération.
SOURCE_FILTERS = {
    "HelloWork": "site:hellowork.com",
    "Indeed": "site:fr.indeed.com",
    "APEC": "site:apec.fr",
    "Welcome": "site:welcometothejungle.com",
    "Meteojob": "site:meteojob.com",
    "Talent": "site:talent.com",
    "LinkedIn Jobs": "site:linkedin.com/jobs",
    "Sites cabinets": "cabinet comptable recrutement paie",
}

DEFAULT_KEYWORDS = [
    "gestionnaire de paie",
    "gestionnaire paie",
    "collaborateur paie",
    "responsable paie",
    "référent paie",
    "silae paie",
    "emploi paie",
    "offre paie",
]

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

PAYROLL_TERMS = [
    "gestionnaire de paie",
    "gestionnaire paie",
    "collaborateur paie",
    "responsable paie",
    "référent paie",
    "referent paie",
    "technicien paie",
    "paie",
    "silae",
    "bulletins",
    "dsn",
]


def _is_useful_url(url):
    if not url:
        return False

    low = url.lower()
    blocked = [
        "google.",
        "bing.",
        "facebook.",
        "instagram.",
        "youtube.",
        "maps.google",
    ]
    return low.startswith("http") and not any(item in low for item in blocked)


def _looks_like_payroll_result(item):
    text = " ".join(
        [
            item.get("title", "") or "",
            item.get("content", "") or "",
            item.get("snippet", "") or "",
            item.get("url", "") or "",
            item.get("link", "") or "",
        ]
    ).lower()

    return any(term in text for term in PAYROLL_TERMS)


def duckduckgo_search(query, max_results=10):
    try:
        response = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        )

        if response.status_code >= 400 or not response.text:
            return []

        results = []

        for match in re.finditer(
            r'class="result__a" href="([^"]+)".*?>(.*?)</a>',
            response.text,
            re.S,
        ):
            href = html.unescape(match.group(1))
            title = re.sub(
                "<.*?>",
                "",
                html.unescape(match.group(2)),
            ).strip()

            if "uddg=" in href:
                href = unquote(
                    parse_qs(urlparse(href).query).get("uddg", [href])[0]
                )

            item = {
                "title": title,
                "content": "",
                "url": href,
            }

            if _is_useful_url(href) and _looks_like_payroll_result(item):
                results.append(item)

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
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": env["google_key"],
                "cx": env["google_cx"],
                "q": query,
                "num": min(max_results, 10),
            },
            timeout=20,
        )

        if response.status_code >= 400 or not (response.text or "").strip():
            return []

        items = []

        for item in response.json().get("items", []) or []:
            result = {
                "title": item.get("title", ""),
                "content": item.get("snippet", ""),
                "url": item.get("link", ""),
            }

            if (
                _is_useful_url(result["url"])
                and _looks_like_payroll_result(result)
            ):
                items.append(result)

        return items

    except Exception:
        return []


def tavily_search(query, max_results=8):
    key = get_env().get("tavily_key", "")

    if not key:
        return []

    try:
        response = requests.post(
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

        if response.status_code >= 400 or not (response.text or "").strip():
            return []

        results = []

        for item in response.json().get("results", []) or []:
            result = {
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "url": item.get("url", ""),
            }

            if (
                _is_useful_url(result["url"])
                and _looks_like_payroll_result(result)
            ):
                results.append(result)

        return results

    except Exception:
        return []


def search_web(query, max_results=10):
    # Tavily en priorité
    results = tavily_search(query, max_results=max_results)

    if results:
        return results, "Tavily"

    results = google_custom_search(query, max_results=max_results)

    if results:
        return results, "Google"

    results = duckduckgo_search(query, max_results=max_results)

    if results:
        return results, "DuckDuckGo"

    return [], "Aucune source"


def guess_department(text):
    text = text or ""

    match = re.search(r"\b([0-9]{2})[0-9]{3}\b", text)

    if match:
        return match.group(1)

    match = re.search(
        r"\b(0[1-9]|[1-8][0-9]|9[0-5])\s*[-–]\s*",
        text,
    )

    if match:
        return match.group(1)

    low = text.lower()

    for department, cities in CITIES_BY_DEP.items():
        for city in cities.split():
            if city.lower() in low:
                return department

    return ""


def guess_city(text):
    cities = []

    for value in CITIES_BY_DEP.values():
        cities.extend(value.split())

    cities += [
        "Paris",
        "Marseille",
        "Bordeaux",
        "Toulouse",
        "Lille",
        "Dijon",
    ]

    low = (text or "").lower()

    for city in cities:
        if city.lower() in low:
            return city

    return ""


def guess_company(title, content):
    blob = f"{title} {content}"

    patterns = [
        r"chez\s+([A-Z][A-Za-zÀ-ÿ0-9&' .-]{2,60})",
        r"recrute\s+([A-Z][A-Za-zÀ-ÿ0-9&' .-]{2,60})",
        r"cabinet\s+([A-Z][A-Za-zÀ-ÿ0-9&' .-]{2,60})",
    ]

    for pattern in patterns:
        match = re.search(pattern, blob)

        if match:
            return clean_company(
                match.group(1).strip(" -|,.;:")
            )

    parts = re.split(r"[-|–]", title or "")

    for part in parts:
        candidate = part.strip()
        low = candidate.lower()

        if (
            len(candidate) > 2
            and "gestionnaire" not in low
            and "paie" not in low
            and "emploi" not in low
        ):
            return clean_company(candidate)

    return "À identifier"


def result_to_prospect(item, source, campaign_id=None):
    title = item.get("title", "") or ""
    content = item.get("content", "") or item.get("snippet", "") or ""
    url = item.get("url", "") or item.get("link", "") or ""
    text = f"{title} {content} {url}"

    company = guess_company(title, content)
    city = guess_city(text)
    department = guess_department(text)
    logiciel = detect_logiciel(text)
    signal = detect_need_signal(text)
    argument = sales_argument(signal, logiciel)
    cabinet_detecte = "Oui" if is_cabinet(text) else "À vérifier"
    recruteur = "Oui" if is_recruiter(company, text) else "Non"
    score = score_offer(text, "CDI", department, company)
    temp = temperature(
        score,
        recruteur,
        cabinet_detecte,
        logiciel,
    )

    return {
        "created_at": str(date.today()),
        "updated_at": str(date.today()),
        "source": source,
        "date_collecte": str(date.today()),
        "priorite": priority(score),
        "score": score,
        "temperature": temp,
        "potentiel_ca": potential_ca(
            score,
            logiciel,
            cabinet_detecte,
        ),
        "prochaine_action": next_action(
            "À contacter",
            temp,
            "",
        ),
        "cabinet": company,
        "cabinet_detecte": cabinet_detecte,
        "recruteur": recruteur,
        "ville": city,
        "departement": department,
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
        "commentaires": f"Trouvé via moteur V19 ({source})",
        "campaign_id": str(campaign_id or ""),
        "is_processed": "0",
    }


def build_queries(departments, keywords):
    clean_keywords = [
        keyword.strip()
        for keyword in keywords
        if keyword.strip()
    ]

    queries = []

    for department in departments:
        cities = CITIES_BY_DEP.get(department, "")

        for keyword in clean_keywords:
            queries.append(
                (
                    "Recherche large",
                    f"{keyword} recrutement emploi {department} {cities}",
                )
            )

            queries.append(
                (
                    "HelloWork",
                    f"site:hellowork.com {keyword} {department} {cities}",
                )
            )

            queries.append(
                (
                    "Indeed",
                    f"site:fr.indeed.com {keyword} {department} {cities}",
                )
            )

            queries.append(
                (
                    "APEC",
                    f"site:apec.fr {keyword} {department} {cities}",
                )
            )

            queries.append(
                (
                    "LinkedIn Jobs",
                    f"site:linkedin.com/jobs {keyword} {department} {cities}",
                )
            )

    return queries


def run_multi_source_watch(
    departments,
    keywords,
    max_results=8,
):
    rows = []
    errors = []
    seen_urls = set()

    campaign_id = create_campaign(
        "Multi-sources V19",
        departments,
        keywords,
    )

    queries = build_queries(
        departments,
        keywords,
    )[:120]

    for source_name, query in queries:
        try:
            results, engine = search_web(
                query,
                max_results=max_results,
            )

            for item in results:
                url = item.get("url") or item.get("link") or ""

                if not url or url in seen_urls:
                    continue

                seen_urls.add(url)

                rows.append(
                    result_to_prospect(
                        item,
                        f"{source_name} / {engine}",
                        campaign_id=campaign_id,
                    )
                )

        except Exception as error:
            errors.append(
                f"{source_name}: {error}"
            )

    inserted, updated = save_prospects(rows)

    update_campaign_counts(
        campaign_id,
        inserted,
        updated,
    )

    if not rows and not errors:
        errors.append(
            "Aucun résultat exploitable trouvé. "
            "Essaie un seul département et 3 à 5 requêtes larges."
        )

    return inserted, updated, errors
