
from datetime import date
from io import BytesIO
import pandas as pd

def _safe_sheet(writer, sheet_name, df):
    if df is None or df.empty:
        pd.DataFrame({"Information": ["Aucune donnée pour cet onglet"]}).to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

def build_excel_export(df):
    output = BytesIO()
    today = str(date.today())
    a_contacter = df[(df["statut"] == "À contacter") & (df["temperature"].isin(["Chaud", "Tiède"]))]
    relances = df[
        ((df["relance_1"].fillna("") <= today) & (df["relance_1"].fillna("") != ""))
        |
        ((df["relance_2"].fillna("") <= today) & (df["relance_2"].fillna("") != ""))
    ]
    chauds = df[df["temperature"] == "Chaud"]
    rdv = df[df["statut"].isin(["Répondu", "RDV", "Client"])]
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        _safe_sheet(writer, "Tous prospects", df)
        _safe_sheet(writer, "A contacter", a_contacter)
        _safe_sheet(writer, "Relances", relances)
        _safe_sheet(writer, "Prospects chauds", chauds)
        _safe_sheet(writer, "Reponses RDV", rdv)
    return output.getvalue()
