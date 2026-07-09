
from urllib.parse import quote_plus

STATUSES = ["À contacter", "Contacté", "Relance 1", "Relance 2", "Répondu", "RDV", "Non intéressé", "Hors cible"]
PRIORITY_DEPARTMENTS = {"26", "07", "38", "69", "42", "44", "35", "49", "85"}

CABINET_SIGNALS = [
    "cabinet comptable", "cabinet d'expertise comptable", "expertise comptable",
    "expert-comptable", "commissariat aux comptes", "fiduciaire",
    "portefeuille clients", "multi-conventions", "multi conventions", "pôle social"
]

RECRUTER_SIGNALS = [
    "apache recrutement", "my premium consulting", "adsearch", "kolibri", "nextep",
    "winsearch", "harry hope", "talents paie", "pay job", "cabexperts",
    "achil", "eclipse", "peakh", "hays", "michael page", "fed group", "randstad",
    "manpower", "adequat", "adecco"
]

KNOWN_COMPANIES = {
    "fiteco": "https://www.fiteco.com",
    "baker tilly": "https://www.bakertilly.fr",
    "endrix": "https://www.endrix.com",
    "in extenso": "https://www.inextenso.fr",
    "tgs france": "https://www.tgs-france.fr",
    "cogedis": "https://www.cogedis.com",
    "compta clemenceau": "https://www.compta-clemenceau.fr",
}

def normalize(value):
    return (value or "").lower()

def clean_company(name):
    if not name:
        return "À identifier"
    low = name.lower()
    if "confidentiel" in low or low.strip() in ["client", "cabinet de recrutement"]:
        return "À identifier"
    return name.strip()

def is_recruiter(company, text):
    t = f"{company} {text}".lower()
    return any(s in t for s in RECRUTER_SIGNALS)

def is_cabinet(text):
    return any(s in normalize(text) for s in CABINET_SIGNALS)

def detect_logiciel(text):
    text_low = normalize(text)
    logiciels = {
        "silae": "Silae", "silaexpert": "Silae", "adp": "ADP", "cegid": "Cegid",
        "sage": "Sage", "quadratus": "Quadratus", "quadra": "Quadratus",
        "isapaye": "ISAPAYE", "isagri": "ISAGRI", "teams rh": "Teams RH",
        "dia paie": "DIA Paie",
    }
    return ", ".join(sorted(set(label for key, label in logiciels.items() if key in text_low)))

def detect_need_signal(text):
    t = normalize(text)
    signals = []
    if "urgent" in t:
        signals.append("Urgence")
    if "remplacement" in t:
        signals.append("Remplacement")
    if "création de poste" in t or "creation de poste" in t:
        signals.append("Création de poste")
    if "croissance" in t or "développement" in t:
        signals.append("Croissance")
    if "portefeuille" in t:
        signals.append("Portefeuille paie")
    if "multi-conventions" in t or "multi conventions" in t:
        signals.append("Multi-conventions")
    if "silae" in t:
        signals.append("Silae")
    return ", ".join(signals) if signals else "Besoin paie"

def sales_argument(signal, logiciel):
    if "Urgence" in signal or "Remplacement" in signal:
        return "continuité de production pendant une période sensible"
    if "Création de poste" in signal or "Croissance" in signal:
        return "renfort souple pendant la structuration du pôle paie"
    if "Silae" in signal or "Silae" in (logiciel or ""):
        return "renfort opérationnel rapidement sur Silae"
    if "Multi-conventions" in signal:
        return "appui sur portefeuille multi-conventions"
    return "sécurisation de la production paie pendant le recrutement"

def score_offer(text, contract, department, company):
    t = normalize(text)
    score = 0
    if "gestionnaire de paie" in t or "gestionnaire paie" in t:
        score += 25
    elif "paie" in t:
        score += 15
    if is_cabinet(t):
        score += 30
    if "portefeuille" in t or "multi-conventions" in t or "multi conventions" in t:
        score += 10
    if "silae" in t or "silaexpert" in t:
        score += 25
    elif any(x in t for x in ["adp", "cegid", "sage", "quadratus", "quadra"]):
        score += 10
    if contract and "cdi" in contract.lower():
        score += 10
    if any(x in t for x in ["urgent", "remplacement", "croissance", "création de poste", "creation de poste"]):
        score += 10
    if department in PRIORITY_DEPARTMENTS:
        score += 5
    if is_recruiter(company, t):
        score -= 20
    if any(x in t for x in ["industrie", "restaurant", "hôtel", "association"]):
        score -= 10
    if "à identifier" in normalize(company):
        score -= 10
    return max(0, min(score, 100))

def priority(score):
    return "Haute" if score >= 75 else "Moyenne" if score >= 50 else "Faible"

def temperature(score, recruteur, cabinet, logiciel):
    if recruteur == "Oui":
        return "À vérifier"
    if score >= 80 and (cabinet == "Oui" or "Silae" in (logiciel or "")):
        return "Chaud"
    if score >= 55:
        return "Tiède"
    return "Froid"

def potential_ca(score, logiciel, cabinet_detecte):
    if score >= 80 and "Silae" in (logiciel or ""):
        return "Fort"
    if score >= 60 and cabinet_detecte == "Oui":
        return "Moyen"
    return "À vérifier"

def next_action(statut, temperature_label, email_public):
    if statut == "À contacter" and temperature_label in ["Chaud", "Tiède"]:
        return "Envoyer mail + LinkedIn" if email_public else "Chercher email / formulaire"
    if statut == "Contacté":
        return "Relance J+7"
    if statut == "Relance 1":
        return "Relance J+21"
    if statut in ["Répondu", "RDV"]:
        return "Suivi opportunité"
    return "À qualifier"

def google_search_url(company, ville):
    company = "" if company == "À identifier" else company
    return "https://www.google.com/search?q=" + quote_plus(f"{company} {ville} cabinet comptable paie contact recrutement".strip())

def linkedin_search_url(company, ville):
    return "https://www.google.com/search?q=" + quote_plus(f"{company} {ville} LinkedIn cabinet comptable".strip())
