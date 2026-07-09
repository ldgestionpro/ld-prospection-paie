
import sqlite3
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

from modules.scoring import next_action

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "ld_prospection.db"

COLUMNS = [
    "created_at", "updated_at", "source", "date_collecte", "priorite", "score", "temperature",
    "potentiel_ca", "prochaine_action", "cabinet", "cabinet_detecte", "recruteur", "ville",
    "departement", "intitule_offre", "type_contrat", "logiciel", "signal_besoin",
    "argument_commercial", "contact_public", "email_public", "telephone", "site_web",
    "linkedin", "page_contact", "recherche_google", "lien_annonce", "statut", "date_contact",
    "relance_1", "relance_2", "dernier_message", "dernier_message_linkedin", "commentaires"
]

def db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _column_type(name):
    return "INTEGER" if name == "score" else "TEXT"

def _ensure_columns(conn):
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(prospects)").fetchall()}
    for col in COLUMNS:
        if col not in existing:
            conn.execute(f"ALTER TABLE prospects ADD COLUMN {col} {_column_type(col)}")

def init_db():
    fields = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT, updated_at TEXT, source TEXT, date_collecte TEXT, priorite TEXT,
        score INTEGER, temperature TEXT, potentiel_ca TEXT, prochaine_action TEXT,
        cabinet TEXT, cabinet_detecte TEXT, recruteur TEXT, ville TEXT, departement TEXT,
        intitule_offre TEXT, type_contrat TEXT, logiciel TEXT, signal_besoin TEXT,
        argument_commercial TEXT, contact_public TEXT, email_public TEXT, telephone TEXT,
        site_web TEXT, linkedin TEXT, page_contact TEXT, recherche_google TEXT,
        lien_annonce TEXT UNIQUE, statut TEXT, date_contact TEXT, relance_1 TEXT,
        relance_2 TEXT, dernier_message TEXT, dernier_message_linkedin TEXT, commentaires TEXT
    """
    with db() as conn:
        conn.execute(f"CREATE TABLE IF NOT EXISTS prospects ({fields})")
        _ensure_columns(conn)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER,
            action_date TEXT,
            action_type TEXT,
            detail TEXT
        )
        """)
        conn.commit()

def add_action(prospect_id, action_type, detail):
    with db() as conn:
        conn.execute(
            "INSERT INTO actions (prospect_id, action_date, action_type, detail) VALUES (?, ?, ?, ?)",
            (prospect_id, str(date.today()), action_type, detail)
        )
        conn.commit()

def save_prospects(rows):
    inserted, updated = 0, 0
    with db() as conn:
        _ensure_columns(conn)
        for row in rows:
            if not row.get("lien_annonce"):
                continue
            clean_row = {c: row.get(c, "") for c in COLUMNS}
            existing = conn.execute("SELECT id FROM prospects WHERE lien_annonce=?", (clean_row["lien_annonce"],)).fetchone()
            if existing:
                updated += 1
                protected = {"lien_annonce", "statut", "date_contact", "relance_1", "relance_2", "commentaires", "dernier_message", "dernier_message_linkedin", "contact_public", "email_public", "telephone"}
                cols = [c for c in COLUMNS if c not in protected]
                set_clause = ", ".join([f"{c}=?" for c in cols])
                conn.execute(f"UPDATE prospects SET {set_clause} WHERE lien_annonce=?", [clean_row[c] for c in cols] + [clean_row["lien_annonce"]])
            else:
                inserted += 1
                placeholders = ", ".join(["?"] * len(COLUMNS))
                conn.execute(f"INSERT INTO prospects ({', '.join(COLUMNS)}) VALUES ({placeholders})", [clean_row[c] for c in COLUMNS])
        conn.commit()
    return inserted, updated

def load_prospects():
    with db() as conn:
        _ensure_columns(conn)
        rows = conn.execute("SELECT * FROM prospects ORDER BY score DESC, id DESC").fetchall()
    return pd.DataFrame([dict(r) for r in rows])

def load_actions():
    with db() as conn:
        rows = conn.execute("SELECT * FROM actions ORDER BY id DESC LIMIT 500").fetchall()
    return pd.DataFrame([dict(r) for r in rows])

def update_status(prospect_id, statut, commentaire=""):
    today = str(date.today())
    fields = {"statut": statut, "updated_at": today}
    if statut == "Contacté":
        fields["date_contact"] = today
        fields["relance_1"] = str(date.today() + timedelta(days=7))
        fields["relance_2"] = str(date.today() + timedelta(days=21))
    if commentaire:
        fields["commentaires"] = commentaire
    with db() as conn:
        current = conn.execute("SELECT temperature, email_public FROM prospects WHERE id=?", (prospect_id,)).fetchone()
        temp = current["temperature"] if current else ""
        email = current["email_public"] if current else ""
        fields["prochaine_action"] = next_action(statut, temp, email)
        set_clause = ", ".join([f"{k}=?" for k in fields])
        conn.execute(f"UPDATE prospects SET {set_clause} WHERE id=?", list(fields.values()) + [prospect_id])
        conn.commit()
    add_action(prospect_id, "Statut", f"{statut} - {commentaire}".strip(" -"))

def save_messages(prospect_id, mail, linkedin):
    with db() as conn:
        conn.execute("UPDATE prospects SET dernier_message=?, dernier_message_linkedin=?, updated_at=? WHERE id=?", (mail, linkedin, str(date.today()), prospect_id))
        conn.commit()
    add_action(prospect_id, "Messages générés", mail[:500])

def update_enriched(row):
    with db() as conn:
        conn.execute(
            "UPDATE prospects SET email_public=?, telephone=?, site_web=?, linkedin=?, page_contact=?, prochaine_action=?, commentaires=?, updated_at=? WHERE id=?",
            (row.get("email_public",""), row.get("telephone",""), row.get("site_web",""),
             row.get("linkedin",""), row.get("page_contact",""), row.get("prochaine_action",""),
             row.get("commentaires",""), str(date.today()), row["id"])
        )
        conn.commit()


def update_prospect_details(prospect_id, updates):
    allowed_fields = {
        "cabinet", "contact_public", "email_public", "telephone", "site_web", "linkedin",
        "page_contact", "statut", "priorite", "temperature", "potentiel_ca", "date_contact",
        "relance_1", "relance_2", "commentaires"
    }
    clean_updates = {key: value for key, value in (updates or {}).items() if key in allowed_fields}
    if not clean_updates:
        return
    clean_updates["updated_at"] = str(date.today())
    with db() as conn:
        _ensure_columns(conn)
        set_clause = ", ".join([f"{key}=?" for key in clean_updates.keys()])
        conn.execute(f"UPDATE prospects SET {set_clause} WHERE id=?", list(clean_updates.values()) + [prospect_id])
        conn.commit()
    add_action(prospect_id, "Fiche prospect", "Mise à jour manuelle")
