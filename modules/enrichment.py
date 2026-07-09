
import html
import re
from urllib.parse import unquote, urlparse, parse_qs
import requests

from modules.config import get_env
from modules.database import load_prospects, update_enriched
from modules.scoring import next_action, google_search_url, linkedin_search_url

BLOCKED_DOMAINS = ["google.", "bing.", "yahoo.", "facebook.", "instagram.", "youtube.", "indeed.", "hellowork.", "francetravail.", "pole-emploi.", "linkedin.com/jobs", "meteojob.", "apec.", "welcometothejungle.", "jobijoba.", "talent.com"]
COMMON_CONTACT_PATHS = ["/contact", "/contacts", "/nous-contacter", "/contactez-nous", "/recrutement", "/carrieres", "/carriere", "/nous-rejoindre", "/offres-emploi", "/emploi"]

def extract_emails(text):
    text = text or ""
    emails = set(re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text))
    cleaned = text.replace(" [at] ", "@").replace("(at)", "@").replace(" arobase ", "@")
    cleaned = cleaned.replace(" [dot] ", ".").replace("(dot)", ".").replace(" point ", ".")
    emails.update(re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", cleaned))
    return sorted(emails)

def extract_phones(text):
    return sorted(set(re.findall(r"(?:(?:\+33|0)\s*[1-9](?:[\s.\-]?\d{2}){4})", text or "")))

def clean_html(html_text):
    text = re.sub(r"<script.*?</script>", " ", html_text or "", flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text))

def is_useful_url(url):
    if not url:
        return False
    low = url.lower()
    return low.startswith("http") and not any(b in low for b in BLOCKED_DOMAINS)

def domain_root(url):
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else ""
    except Exception:
        return ""

def tavily_search(query, max_results=6):
    key = get_env().get("tavily_key", "")
    if not key:
        return []
    try:
        r = requests.post("https://api.tavily.com/search", json={"api_key": key, "query": query, "search_depth": "advanced", "max_results": max_results, "include_answer": False, "include_raw_content": False}, timeout=25)
        if r.status_code >= 400 or not (r.text or "").strip():
            return []
        return [{"title": i.get("title",""), "snippet": i.get("content",""), "link": i.get("url","")} for i in r.json().get("results", []) if is_useful_url(i.get("url",""))]
    except Exception:
        return []

def google_custom_search(query, num=5):
    env = get_env()
    if not env.get("google_key") or not env.get("google_cx"):
        return []
    try:
        r = requests.get("https://www.googleapis.com/customsearch/v1", params={"key": env["google_key"], "cx": env["google_cx"], "q": query, "num": num}, timeout=20)
        if r.status_code >= 400 or not (r.text or "").strip():
            return []
        return [{"title": i.get("title",""), "snippet": i.get("snippet",""), "link": i.get("link","")} for i in r.json().get("items", []) or []]
    except Exception:
        return []

def duckduckgo_search(query, max_results=8):
    try:
        r = requests.get("https://duckduckgo.com/html/", params={"q": query}, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        if r.status_code >= 400 or not r.text:
            return []
        results = []
        for match in re.finditer(r'class="result__a" href="([^"]+)".*?>(.*?)</a>', r.text, re.S):
            href = html.unescape(match.group(1))
            title = re.sub("<.*?>", "", html.unescape(match.group(2))).strip()
            if "uddg=" in href:
                href = unquote(parse_qs(urlparse(href).query).get("uddg", [href])[0])
            if is_useful_url(href):
                results.append({"title": title, "snippet": "", "link": href})
            if len(results) >= max_results:
                break
        return results
    except Exception:
        return []

def fetch_page(url):
    if not is_useful_url(url):
        return ""
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12, allow_redirects=True)
        if r.status_code >= 400:
            return ""
        return r.text[:200000]
    except Exception:
        return ""

def choose_best_site(items, company):
    company_low = (company or "").lower()
    candidates = []
    for item in items:
        link = item.get("link", "")
        root = domain_root(link)
        if not is_useful_url(link) or not root:
            continue
        score = 0
        blob = (item.get("title","") + " " + item.get("snippet","") + " " + link).lower()
        for word in re.findall(r"[a-zA-ZÀ-ÿ0-9]+", company_low):
            if len(word) > 3 and word in blob: score += 2
            if len(word) > 3 and word in root.lower(): score += 4
        if any(k in blob for k in ["cabinet", "expertise comptable", "paie", "contact", "recrutement"]): score += 2
        candidates.append((score, root, link))
    if not candidates:
        return "", ""
    candidates.sort(reverse=True)
    return candidates[0][1], candidates[0][2]

def get_contact_pages(site_root):
    return [site_root.rstrip("/") + path for path in COMMON_CONTACT_PATHS] if site_root else []

def enrich_one(row):
    enriched = dict(row)
    company = row.get("cabinet", "")
    ville = row.get("ville", "")
    enriched["recherche_google"] = enriched.get("recherche_google") or google_search_url(company, ville)
    enriched["linkedin"] = enriched.get("linkedin") or linkedin_search_url(company, ville)

    query = f"{company} {ville} cabinet comptable contact recrutement email téléphone"
    items = tavily_search(query, 8)
    source = "Tavily"
    if not items:
        items = google_custom_search(query, 8); source = "Google"
    if not items:
        items = duckduckgo_search(query, 8); source = "DuckDuckGo"
    if not items:
        enriched["commentaires"] = ((enriched.get("commentaires") or "") + " | Enrichissement: aucun résultat web").strip(" |")
        return enriched

    site_root, first_url = choose_best_site(items, company)
    if site_root and not enriched.get("site_web"):
        enriched["site_web"] = site_root

    linkedin_links = [i.get("link","") for i in items if "linkedin.com/company" in i.get("link","")]
    if linkedin_links:
        enriched["linkedin"] = linkedin_links[0]

    texts = [" ".join((i.get("title","") + " " + i.get("snippet","")) for i in items)]
    urls_to_try = ([first_url] if first_url else []) + get_contact_pages(enriched.get("site_web", ""))
    found_contact = ""
    for url in urls_to_try[:10]:
        page = fetch_page(url)
        if page:
            texts.append(clean_html(page))
            if not found_contact and any(k in url.lower() for k in ["contact", "recrut", "carriere", "emploi"]):
                found_contact = url

    combined = " ".join(texts)
    emails = extract_emails(combined)
    phones = extract_phones(combined)

    if emails and not enriched.get("email_public"):
        preferred = [e for e in emails if any(k in e.lower() for k in ["contact", "recrut", "rh", "social", "info", "accueil"])]
        enriched["email_public"] = (preferred or emails)[0]
    if phones and not enriched.get("telephone"):
        enriched["telephone"] = phones[0]
    if not enriched.get("page_contact"):
        enriched["page_contact"] = found_contact or (get_contact_pages(enriched.get("site_web", ""))[0] if enriched.get("site_web") else "")

    enriched["prochaine_action"] = next_action(enriched.get("statut","À contacter"), enriched.get("temperature",""), enriched.get("email_public",""))
    enriched["commentaires"] = ((enriched.get("commentaires") or "") + f" | Enrichissement via {source}").strip(" |")
    return enriched

def enrich_best_prospects(limit=10):
    df = load_prospects()
    if df.empty:
        return 0
    targets = df[(df["statut"] == "À contacter") & (df["temperature"].isin(["Chaud", "Tiède"]))].head(limit)
    count = 0
    for _, row in targets.iterrows():
        update_enriched(enrich_one(row.to_dict()))
        count += 1
    return count
