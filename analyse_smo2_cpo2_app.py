
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from analyse_smo2_cpo2_reportlab import generate_pdf
import tempfile
import os

st.set_page_config(layout="wide")
st.title("🧪 Rapport complet CPO2 – SmO₂ & PDF")

txt_file = st.file_uploader("📄 Fichier .txt du sportif", type=["txt"])
excel_file = st.file_uploader("📊 Données Excel (.xlsx)", type=["xlsx"])

remarques = st.text_area("🖊️ Remarques du testeur", "Test réalisé sans incident. Cinétique attendue. Bon retour veineux.")

if txt_file and excel_file:
    # Lecture txt
    identity = {}
    for line in txt_file.read().decode("utf-8").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            identity[k.strip()] = v.strip()
    poids_kg = float(identity.get("Weight", "70").split()[0])

    # Lecture Excel
    xls = pd.ExcelFile(excel_file)
    sheet = st.selectbox("Feuille de données", xls.sheet_names)
    df = xls.parse(sheet)
    df = df.dropna()

    time_col = st.selectbox("Temps (s)", [c for c in df.columns if "Time" in c])
    smo2_col = st.selectbox("SmO₂", [c for c in df.columns if "SmO2" in c])
    power_col = st.selectbox("Puissance", [c for c in df.columns if "Power" in c or "Target" in c])
    hr_col = st.selectbox("Fréquence cardiaque", [c for c in df.columns if "HR" in c or "Fréquence" in c])

    df = df[[time_col, smo2_col, power_col, hr_col]]
    df.columns = ["Time", "SmO2", "Power", "HR"]
    df["SmO2_norm"] = 100 * (df["SmO2"] - df["SmO2"].min()) / (df["SmO2"].max() - df["SmO2"].min())

    s1 = st.slider("Position S1 (s)", int(df["Time"].min()), int(df["Time"].max()), int(df["Time"].min()) + 200)
    s2 = st.slider("Position S2 (s)", int(df["Time"].min()), int(df["Time"].max()), int(df["Time"].min()) + 600)
    pma = st.slider("Position PMA (s)", int(df["Time"].min()), int(df["Time"].max()), int(df["Time"].max()) - 100)

    def get_values_at(t):
        row = df.iloc[(df["Time"] - t).abs().argmin()]
        return {
            "power": int(row["Power"]),
            "hr": int(row["HR"]),
            "smo2": round(float(row["SmO2"]), 1),
            "wkg": round(float(row["Power"]) / poids_kg, 2)
        }

    s1_vals = get_values_at(s1)
    s2_vals = get_values_at(s2)
    pma_vals = get_values_at(pma)

    seuils = {"S1": s1_vals, "S2": s2_vals, "PMA": pma_vals}
    zones = [
        {"zone": "Z1", "puissance": f"< {s1_vals['power']} W", "wkg": f"< {s1_vals['wkg']}", "description": "Endurance basse intensité"},
        {"zone": "Z2", "puissance": f"{s1_vals['power']}–{s2_vals['power']} W", "wkg": f"{s1_vals['wkg']}–{s2_vals['wkg']}", "description": "Zone aérobie"},
        {"zone": "Z3", "puissance": f"> {s2_vals['power']} W", "wkg": f"> {s2_vals['wkg']}", "description": "Haute intensité"},
    ]

    # Graphique
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Time"], df["SmO2_norm"], color='blue', label='SmO₂ normalisée (%)')
    ax.axvline(s1, color='green', linestyle='--', label='S1')
    ax.axvline(s2, color='red', linestyle='--', label='S2')
    ax.axvline(pma, color='black', linestyle='--', label='PMA')
    ax.fill_between(df["Time"], 0, 100, where=df["Time"] < s1, color="green", alpha=0.1)
    ax.fill_between(df["Time"], 0, 100, where=(df["Time"] >= s1) & (df["Time"] < s2), color="orange", alpha=0.1)
    ax.fill_between(df["Time"], 0, 100, where=(df["Time"] >= s2) & (df["Time"] < pma), color="red", alpha=0.1)
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("SmO₂ normalisée (%)")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

    # Sauvegarde graphique
    graph_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(graph_temp.name)

    # Logo auto
    logo_path = "logo CPO2_06_CMJN.jpg"
    if not os.path.exists(logo_path):
        st.warning("⚠️ Le logo 'logo CPO2_06_CMJN.jpg' est manquant dans le dossier.")
        logo_path = None

    # Générer le PDF
    if st.button("📄 Générer le rapport PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            try:
                generate_pdf(tmp_pdf.name, identity, seuils, zones, remarques,
                             graph_path=graph_temp.name, logo_path=logo_path)
                with open(tmp_pdf.name, "rb") as f:
                    st.download_button("📥 Télécharger le rapport PDF", f, file_name=f"{identity.get('Athlete Name', 'rapport')}_CPO2.pdf")
                    st.success("✅ Rapport généré avec succès.")
            except Exception as e:
                st.error(f"Erreur PDF : {e}")
