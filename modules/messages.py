def _clean(value):
    return (value or "").strip()


def _contains(text, keywords):
    text = (text or "").lower()
    return any(keyword.lower() in text for keyword in keywords)


def _job_title(row):
    title = _clean(row.get("intitule_offre"))
    title_low = title.lower()

    if "responsable paie" in title_low:
        return "responsable paie"
    if "collaborateur paie" in title_low:
        return "collaborateur paie"
    if "gestionnaire de paie" in title_low or "gestionnaire paie" in title_low:
        return "gestionnaire de paie"
    if "référent paie" in title_low or "referent paie" in title_low:
        return "référent paie"

    return "profil paie"


def _software_sentence(logiciel):
    logiciel = _clean(logiciel)

    if not logiciel:
        return ""

    if "Silae" in logiciel:
        return (
            "\n\nVotre environnement Silae est un vrai point de repère : "
            "je peux m’intégrer plus rapidement à vos process et être opérationnelle sans longue phase de prise en main."
        )

    if "Cegid" in logiciel:
        return (
            "\n\nLa mention de Cegid me permet également d’adapter mon accompagnement à votre environnement de travail."
        )

    if "Sage" in logiciel:
        return (
            "\n\nLa mention de Sage me permet également d’adapter mon accompagnement à votre environnement de travail."
        )

    if "ADP" in logiciel:
        return (
            "\n\nLa mention d’ADP me permet également d’adapter mon accompagnement à votre environnement de travail."
        )

    return (
        f"\n\nLa mention de {logiciel} me permettrait d’adapter mon accompagnement à votre environnement de travail."
    )


def _context_sentence(row):
    signal = _clean(row.get("signal_besoin"))
    text = " ".join(
        [
            _clean(row.get("intitule_offre")),
            _clean(row.get("signal_besoin")),
            _clean(row.get("argument_commercial")),
            _clean(row.get("commentaires")),
        ]
    )

    if _contains(text, ["création de poste", "creation de poste", "structuration"]):
        return (
            "Lorsqu’un cabinet structure ou renforce son pôle social, "
            "un appui temporaire peut permettre de sécuriser la production tout en laissant le temps au recrutement d’aboutir."
        )

    if _contains(text, ["remplacement", "absence", "congé", "maladie"]):
        return (
            "Dans une période de remplacement ou d’absence, la priorité est souvent de maintenir les échéances paie et DSN "
            "sans mettre l’équipe en tension."
        )

    if _contains(text, ["croissance", "développement", "renfort", "portefeuille"]):
        return (
            "Lorsque le portefeuille paie se développe, un renfort externe peut aider à absorber la charge "
            "sans désorganiser l’équipe en place."
        )

    if signal:
        return (
            "Dans ce type de contexte, il peut être utile de disposer d’un soutien opérationnel "
            "pour maintenir la qualité de service et respecter les délais clients."
        )

    return (
        "Lorsqu’un cabinet recrute sur la paie, il peut être utile de disposer d’un soutien opérationnel "
        "pour assurer la continuité de service pendant la période de transition."
    )


def _opening_sentence(row):
    ville = _clean(row.get("ville"))
    poste = _job_title(row)

    if ville:
        return f"J’ai remarqué que vous recherchez actuellement un(e) {poste} à {ville}."
    return f"J’ai remarqué que vous recherchez actuellement un(e) {poste}."


def build_mail(row, variant="agent"):
    ville = _clean(row.get("ville"))
    logiciel = _clean(row.get("logiciel"))
    opening = _opening_sentence(row)
    context = _context_sentence(row)
    logiciel_sentence = _software_sentence(logiciel)

    if variant == "court":
        return f"""Bonjour,

{opening}

Gestionnaire de paie indépendante, j’interviens en renfort ou en marque blanche auprès des cabinets comptables afin de sécuriser la production des bulletins, les DSN, les entrées/sorties et l’administration du personnel.{logiciel_sentence}

Un renfort ponctuel pourrait-il vous être utile pendant votre recrutement ?

Bien cordialement,

Lucia Deloche
LD Gestion Pro
Votre sérénité, ma priorité.
"""

    if variant == "relance":
        return """Bonjour,

Je reviens vers vous suite à mon précédent message concernant un éventuel besoin de renfort paie.

Si votre recrutement est toujours en cours, LD Gestion Pro peut intervenir ponctuellement pour sécuriser la production des bulletins, les DSN, les entrées/sorties ou la reprise de dossiers.

Seriez-vous disponible pour un échange rapide ?

Bien cordialement,

Lucia Deloche
LD Gestion Pro
"""

    if variant == "cabinet":
        return f"""Bonjour,

{opening}

{context}

Gestionnaire de paie indépendante, j’interviens en marque blanche auprès des cabinets comptables pour prendre en charge tout ou partie de la production sociale : bulletins, DSN, administration du personnel, entrées et sorties des salariés, ainsi que reprise de dossiers.{logiciel_sentence}

Mon intervention reste discrète, flexible et alignée sur vos process internes.

Si cette solution peut répondre à un besoin actuel ou à venir, je serais ravie d’échanger avec vous quelques minutes.

Bien cordialement,

Lucia Deloche
LD Gestion Pro
Gestionnaire de paie confirmée – partenaire externe
Votre sérénité, ma priorité.
"""

    return f"""Bonjour,

{opening}

{context}

Pendant que vous finalisez votre recrutement, LD Gestion Pro peut intervenir en renfort externe ou en marque blanche afin de sécuriser la production paie sans alourdir votre organisation interne.

J’interviens sur la production des bulletins, les DSN, l’administration du personnel, les entrées et sorties des salariés, ainsi que la reprise de dossiers.{logiciel_sentence}

Si un renfort ponctuel ou temporaire peut vous être utile, je serais ravie d’en échanger avec vous.

Bien cordialement,

Lucia Deloche
LD Gestion Pro
Gestionnaire de paie confirmée – partenaire externe
Votre sérénité, ma priorité.
"""


def build_linkedin_message(row):
    ville = _clean(row.get("ville"))
    logiciel = _clean(row.get("logiciel"))
    poste = _job_title(row)

    location = f" à {ville}" if ville else ""
    logiciel_part = f", notamment sur {logiciel}" if logiciel else ""

    return f"""Bonjour,

J’ai vu que votre structure recherchait actuellement un(e) {poste}{location}.

J’interviens en renfort externe ou en marque blanche auprès des cabinets comptables pour sécuriser la production paie pendant les périodes de recrutement ou de surcharge{logiciel_part}.

Un soutien ponctuel pourrait-il vous être utile ?
"""