def build_mail(row, variant="agent"):
    ville = row.get("ville") or ""
    logiciel = row.get("logiciel") or ""

    logiciel_phrase = (
        f"\n\nVotre utilisation de {logiciel} me permettrait d'être rapidement opérationnelle et de m'intégrer facilement à votre organisation."
        if logiciel
        else ""
    )

    if variant == "court":
        return f"""Bonjour,

J'ai remarqué que vous recrutez actuellement un profil paie{" à " + ville if ville else ""}.

Gestionnaire de paie indépendante, j'interviens en renfort ou en marque blanche auprès des cabinets comptables afin de sécuriser la production des bulletins, les DSN, les entrées/sorties et l'administration du personnel.{logiciel_phrase}

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

J'ai remarqué que vous recrutez actuellement un profil paie{" à " + ville if ville else ""}.

Lorsqu'un cabinet renforce son équipe paie, il peut être utile de s'appuyer temporairement sur un renfort opérationnel afin de maintenir la qualité de service et de respecter les délais clients.

Gestionnaire de paie indépendante, j'interviens en marque blanche auprès des cabinets comptables pour prendre en charge la production des bulletins, les DSN, l'administration du personnel, les entrées et sorties des salariés ainsi que la reprise de dossiers.{logiciel_phrase}

Mon intervention reste discrète, flexible et alignée sur vos process internes.

Si un renfort ponctuel peut vous être utile pendant votre recrutement, je serais ravie d'échanger avec vous.

Bien cordialement,

Lucia Deloche
LD Gestion Pro
Gestionnaire de paie confirmée – partenaire externe
Votre sérénité, ma priorité.
"""

    return f"""Bonjour,

J'ai remarqué que vous recrutez actuellement un profil paie{" à " + ville if ville else ""}.

Lorsqu'un cabinet renforce ou structure son pôle social, il peut être utile de disposer d'un soutien opérationnel afin de sécuriser la production des paies et d'éviter toute tension sur les délais.

Gestionnaire de paie indépendante, j'interviens en marque blanche auprès des cabinets comptables pour prendre en charge la production des bulletins, les DSN, l'administration du personnel, les entrées et sorties des salariés, ainsi que la reprise de dossiers.{logiciel_phrase}

Si un renfort ponctuel ou temporaire peut vous être utile pendant votre recrutement, je serais ravie d'en échanger avec vous.

Bien cordialement,

Lucia Deloche
LD Gestion Pro
Gestionnaire de paie confirmée – partenaire externe
Votre sérénité, ma priorité.
"""


def build_linkedin_message(row):
    ville = row.get("ville") or ""
    logiciel = row.get("logiciel") or ""

    logiciel_part = f" sur {logiciel}" if logiciel else ""

    return f"""Bonjour,

J'ai vu que votre structure recrute actuellement un profil paie{" à " + ville if ville else ""}.

J'interviens en renfort externe ou en marque blanche auprès des cabinets comptables pour sécuriser la production pendant les périodes de recrutement ou de surcharge{logiciel_part}.

Un soutien ponctuel pourrait-il vous être utile ?
"""