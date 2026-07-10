
from datetime import date
import requests

from modules.config import get_env
from modules.database import save_prospects, create_campaign, update_campaign_counts
from modules.scoring import (
    clean_company, detect_logiciel, detect_need_signal, google_search_url, is_cabinet,
    is_recruiter, linkedin_search_url, potential_ca, priority, sales_argument,
    score_offer, temperature, next_action, KNOWN_COMPANIES
)

FT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
FT_SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

def _safe_json(response):
    text = response.text or ""
    if not text.strip():
        raise RuntimeError(f"Réponse vide de l’API. Statut HTTP : {response.status_code}")
    try:
        return response.json()
    except Exception:
        preview = text[:250].replace("\n", " ")
        raise RuntimeError(f"Réponse API non JSON. Statut {response.status_code}. Aperçu : {preview}")

def get_token():
    env = get_env()
    if not env["ft_client_id"] or not env["ft_client_secret"]:
        raise RuntimeError("Identifiants France Travail manquants.")
    data = {
        "grant_type": "client_credentials",
        "client_id": env["ft_client_id"],
        "client_secret": env["ft_client_secret"],
        "scope": "api_offresdemploiv2 o2dsoffre"
    }
    r = requests.post(FT_TOKEN_URL, data=data, timeout=30)
    if r.status_code >= 400:
        preview = (r.text or "")[:250].replace("\n", " ")
        raise RuntimeError(f"Erreur token France Travail {r.status_code} : {preview}")
    data_json = _safe_json(r)
    token = data_json.get("access_token")
    if not token:
        raise RuntimeError(f"Token absent dans la réponse France Travail : {data_json}")
    return token

def search_offers(token, keywords, department, max_results):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"motsCles": keywords, "departement": department, "sort": 1, "range": f"0-{max_results-1}"}
    r = requests.get(FT_SEARCH_URL, headers=headers, params=params, timeout=30)
    if r.status_code == 204 or not (r.text or "").strip():
        return []
    if r.status_code >= 400:
        preview = (r.text or "")[:200].replace("\n", " ")
        raise RuntimeError(f"Erreur recherche France Travail {r.status_code} pour '{keywords}' / {department} : {preview}")
    data = _safe_json(r)
    return data.get("resultats", []) or []

def offer_to_prospect(offer, campaign_id=None):
    entreprise = offer.get("entreprise") or {}
    lieu = offer.get("lieuTravail") or {}
    contrat = offer.get("typeContrat") or ""
    desc = offer.get("description") or ""
    title = offer.get("intitule") or ""
    company = clean_company(entreprise.get("nom"))
    ville = lieu.get("libelle") or ""
    dep = lieu.get("codePostal", "")[:2] if lieu.get("codePostal") else ""
    text = " ".join([title, desc, company, ville, contrat])
    score = score_offer(text, contrat, dep, company)
    logiciel = detect_logiciel(text)
    signal = detect_need_signal(text)
    argument = sales_argument(signal, logiciel)
    cabinet_detecte = "Oui" if is_cabinet(text) else "À vérifier"
    recruteur = "Oui" if is_recruiter(company, text) else "Non"
    temp = temperature(score, recruteur, cabinet_detecte, logiciel)
    lien = offer.get("origineOffre", {}).get("urlOrigine") or offer.get("urlPostulation") or ""
    site = next((url for key, url in KNOWN_COMPANIES.items() if key in company.lower()), "")
    return {
        "created_at": str(date.today()), "updated_at": str(date.today()),
        "source": "France Travail", "date_collecte": str(date.today()),
        "priorite": priority(score), "score": score, "temperature": temp,
        "potentiel_ca": potential_ca(score, logiciel, cabinet_detecte),
        "prochaine_action": next_action("À contacter", temp, ""),
        "cabinet": company, "cabinet_detecte": cabinet_detecte, "recruteur": recruteur,
        "ville": ville, "departement": dep, "intitule_offre": title,
        "type_contrat": contrat, "logiciel": logiciel, "signal_besoin": signal,
        "argument_commercial": argument, "contact_public": "", "email_public": "",
        "telephone": "", "site_web": site, "linkedin": linkedin_search_url(company, ville),
        "page_contact": "", "recherche_google": google_search_url(company, ville),
        "lien_annonce": lien, "statut": "À contacter", "date_contact": "",
        "relance_1": "", "relance_2": "", "dernier_message": "",
        "dernier_message_linkedin": "", "commentaires": "",
        "campaign_id": str(campaign_id or ""),
        "is_processed": "0",
    }

def run_watch(keywords, departments, max_results):
    token = get_token()
    rows, errors = [], []

    campaign_id = create_campaign("France Travail", departments, keywords)

    for keyword in keywords:
        for department in departments:
            try:
                offers = search_offers(
                    token,
                    keyword,
                    department,
                    max_results,
                )
                rows.extend(
                    [
                        offer_to_prospect(
                            offer,
                            campaign_id=campaign_id,
                        )
                        for offer in offers
                    ]
                )
            except Exception as error:
                errors.append(f"{keyword} / {department} : {error}")

    inserted, updated = save_prospects(rows)
    update_campaign_counts(campaign_id, inserted, updated)
    return inserted, updated, errors
