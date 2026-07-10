def _clean(value):
    return str(value or "").strip()


def _contains(text, keywords):
    text = _clean(text).lower()
    return any(keyword.lower() in text for keyword in keywords)


def _job_title(row):
    title = _clean(row.get("intitule_offre")).lower()

    if "responsable paie" in title:
        return "responsable paie"
    if "collaborateur paie" in title:
        return "collaborateur paie"
    if "référent paie" in title or "referent paie" in title:
        return "référent paie"
    if "gestionnaire de paie" in title or "gestionnaire paie" in title:
        return "gestionnaire de paie"

    return "profil paie"


def _opening(row):
    cabinet = _clean(row.get("cabinet"))
    ville = _clean(row.get("ville"))
    poste = _job_title(row)

    if cabinet and cabinet != "À identifier":
        if ville:
            return (
                f"J’ai remarqué que {cabinet} recherche actuellement "
                f"un(e) {poste} à {ville}."
            )
        return (
            f"J’ai remarqué que {cabinet} recherche actuellement "
            f"un(e) {poste}."
        )

    if ville:
        return (
            f"J’ai remarqué que vous recherchez actuellement "
            f"un(e) {poste} à {ville}."
        )

    return (
        f"J’ai remarqué que vous recherchez actuellement "
        f"un(e) {poste}."
    )


def _context(row):
    text = " ".join(
        [
            _clean(row.get("intitule_offre")),
            _clean(row.get("signal_besoin")),
            _clean(row.get("argument_commercial")),
            _clean(row.get("commentaires")),
        ]
    )

    if _contains(
        text,
        ["remplacement", "absence", "congé maternité", "arrêt maladie"],
    ):
        return (
            "Dans ce type de période, l’enjeu est souvent de maintenir "
            "les échéances de paie et de DSN sans mettre l’équipe en tension."
        )

    if _contains(
        text,
        ["création de poste", "creation de poste", "structuration"],
    ):
        return (
            "Lorsqu’un cabinet structure ou renforce son pôle social, "
            "un appui temporaire peut permettre de sécuriser la production "
            "tout en laissant le temps au recrutement d’aboutir."
        )

    if _contains(
        text,
        ["croissance", "développement", "augmentation du portefeuille"],
    ):
        return (
            "Dans un contexte de croissance, un renfort externe peut aider "
            "à absorber la charge sans désorganiser l’équipe en place."
        )

    if _contains(
        text,
        ["portefeuille", "multi-conventions", "multi conventions"],
    ):
        return (
            "La gestion d’un portefeuille paie demande une continuité "
            "de production et une vigilance constante sur les échéances clients."
        )

    return (
        "Pendant un recrutement, un renfort opérationnel peut permettre "
        "de préserver la continuité de service et le respect des délais clients."
    )


def _software_sentence(row):
    logiciel = _clean(row.get("logiciel"))

    if not logiciel:
        return ""

    logiciel_lower = logiciel.lower()

    if "silae" in logiciel_lower:
        return (
            "\n\nMa maîtrise de Silae me permettrait de m’intégrer rapidement "
            "à vos méthodes de travail et d’être opérationnelle sans longue "
            "phase de prise en main."
        )

    if "cegid" in logiciel_lower:
        return (
            "\n\nLa mention de Cegid me permet également d’adapter rapidement "
            "mon intervention à votre environnement de travail."
        )

    if "sage" in logiciel_lower:
        return (
            "\n\nLa mention de Sage me permet également d’adapter rapidement "
            "mon intervention à votre environnement de travail."
        )

    if "adp" in logiciel_lower:
        return (
            "\n\nLa mention d’ADP me permet également d’adapter rapidement "
            "mon intervention à votre environnement de travail."
        )

    return (
        f"\n\nLa mention de {logiciel} me permettra d’adapter mon intervention "
        "à votre environnement de travail."
    )


def build_subject(row):
    ville = _clean(row.get("ville"))
    logiciel = _clean(row.get("logiciel"))

    if logiciel and ville:
        return f"Renfort paie pendant votre recrutement à {ville}"

    if ville:
        return f"Renfort paie pendant votre recrutement à {ville}"

    return "Renfort paie pendant votre recrutement"


def build_mail(row, variant="agent"):
    opening = _opening(row)
    context = _context(row)
    software = _software_sentence(row)

    if variant == "court":
        return f"""Bonjour,

{opening}

Gestionnaire de paie indépendante, j’interviens en renfort ou en marque blanche auprès des cabinets comptables afin de sécuriser la production des bulletins, les DSN, les entrées et sorties ainsi que l’administration du personnel.{software}

Un renfort ponctuel pourrait-il vous être utile pendant votre recrutement ?

Bien cordialement,

Lucia Deloche
LD Gestion Pro
Votre sérénité, ma priorité.
"""

    if variant == "relance":
        return """Bonjour,

Je reviens vers vous à la suite de mon précédent message concernant un éventuel besoin de renfort paie.

Si votre recrutement est toujours en cours, je peux intervenir ponctuellement afin de sécuriser la production des bulletins, les DSN, les entrées et sorties ou la reprise de dossiers.

Seriez-vous disponible pour un échange rapide ?

Bien cordialement,

Lucia Deloche
LD Gestion Pro
"""

    if variant == "cabinet":
        return f"""Bonjour,

{opening}

{context}

Gestionnaire de paie indépendante, j’interviens en marque blanche auprès des cabinets comptables pour prendre en charge tout ou partie de la production sociale : bulletins, DSN, administration du personnel, entrées et sorties des salariés ainsi que reprise de dossiers.{software}

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

J’interviens sur la production des bulletins, les DSN, l’administration du personnel, les entrées et sorties des salariés ainsi que la reprise de dossiers.{software}

Si un renfort ponctuel ou temporaire peut vous être utile, je serais ravie d’en échanger avec vous.

Bien cordialement,

Lucia Deloche
LD Gestion Pro
Gestionnaire de paie confirmée – partenaire externe
Votre sérénité, ma priorité.
"""


def build_linkedin_message(row):
    ville = _clean(row.get("ville"))
    poste = _job_title(row)
    logiciel = _clean(row.get("logiciel"))

    location = f" à {ville}" if ville else ""
    software = f", notamment sur {logiciel}" if logiciel else ""

    return f"""Bonjour,

J’ai vu que votre structure recherchait actuellement un(e) {poste}{location}.

J’interviens en renfort externe ou en marque blanche auprès des cabinets comptables pour sécuriser la production paie pendant les périodes de recrutement ou de surcharge{software}.

Un soutien ponctuel pourrait-il vous être utile ?
"""