
def build_mail(row, variant="agent"):
    ville = row.get("ville") or ""
    logiciel = row.get("logiciel") or ""
    cabinet = row.get("cabinet") or "votre cabinet"
    signal = row.get("signal_besoin") or "besoin paie"
    argument = row.get("argument_commercial") or "sécurisation de la production paie"
    logiciel_phrase = f" J’ai noté la mention de {logiciel}, ce qui peut permettre une prise en main plus rapide." if logiciel else ""
    site_phrase = f"\nJ’ai également consulté votre site ({row.get('site_web')}) afin de mieux situer votre environnement." if row.get("site_web") else ""
    intro = f"{cabinet} semble recruter actuellement un profil paie à {ville}" if cabinet != "À identifier" else f"Votre cabinet semble recruter actuellement un profil paie à {ville}"

    if variant == "court":
        return f"""Bonjour,

{intro}. LD Gestion Pro peut intervenir en renfort externe ou en marque blanche pour assurer la {argument}.{logiciel_phrase}

Seriez-vous ouverte/ouvert à un échange rapide pour voir si un soutien ponctuel peut vous être utile ?

Lucia
LD Gestion Pro
Gestionnaire de paie confirmée – partenaire externe
Votre sérénité, ma priorité"""

    if variant == "relance":
        return """Bonjour,

Je reviens vers vous suite à mon précédent message concernant votre besoin de renfort paie.

Si votre recrutement est toujours en cours, LD Gestion Pro peut intervenir ponctuellement pour sécuriser la production, les DSN, les entrées/sorties ou la reprise de dossiers.

Un échange rapide vous permettrait-il de voir si cela peut vous soulager sur la période ?

Lucia
LD Gestion Pro"""

    if variant == "cabinet":
        return f"""Bonjour,

{intro}. Le signal principal que j’ai relevé est : {signal}.{site_phrase}

Lorsqu’un cabinet recrute en paie, l’enjeu est souvent de maintenir la production sociale sans dégrader les délais clients. LD Gestion Pro peut intervenir en renfort externe ou en marque blanche pour assurer la {argument}.{logiciel_phrase}

Mon intervention reste discrète, alignée sur vos process, et peut couvrir les bulletins, DSN, entrées/sorties, dossiers salariés et reprise de dossiers.

Seriez-vous disponible pour un échange rapide cette semaine ?

Lucia
LD Gestion Pro
Gestionnaire de paie confirmée – partenaire externe
Votre sérénité, ma priorité"""

    return f"""Bonjour,

{intro}. Le signal principal que j’ai relevé est : {signal}. Dans ce contexte, LD Gestion Pro peut intervenir en renfort externe ou en marque blanche pour assurer la {argument}.{logiciel_phrase}

J’interviens auprès des cabinets comptables sur la production des bulletins, DSN, entrées/sorties, administration du personnel et reprise de dossiers.

L’objectif est simple : maintenir la continuité de service sans alourdir votre organisation interne, le temps que votre recrutement aboutisse.

Seriez-vous ouverte/ouvert à un échange rapide pour voir si un renfort ponctuel pourrait vous être utile ?

Lucia
LD Gestion Pro
Gestionnaire de paie confirmée – partenaire externe
Votre sérénité, ma priorité"""

def build_linkedin_message(row):
    ville = row.get("ville") or ""
    logiciel = row.get("logiciel") or ""
    signal = row.get("signal_besoin") or "besoin paie"
    logiciel_part = f" notamment sur {logiciel}" if logiciel else ""
    return f"""Bonjour,

J’ai vu que votre structure recrute actuellement sur la paie à {ville}. Le besoin semble lié à : {signal}.

J’interviens en renfort externe / marque blanche pour les cabinets comptables afin de sécuriser la production pendant les périodes de recrutement ou de surcharge{logiciel_part}.

Est-ce qu’un soutien ponctuel pourrait vous être utile ?"""
