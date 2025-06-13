
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
from analyse_smo2_cpo2_reportlab import generate_pdf
import tempfile
import os

st.set_page_config(layout="wide")
st.title("🧪 Rapport CPO2 – SmO₂")

txt_file = st.file_uploader("📄 Charger le fichier .txt", type=["txt"])
excel_file = st.file_uploader("📊 Charger le fichier Excel (.xlsx)", type=["xlsx"])

remarques = st.text_area("🖊️ Remarques", "Bonne stabilité jusqu’à S2, réoxygénation rapide post-PMA.")

if txt_file and excel_file:
    identity = {}
    for line in txt_file.read().decode("utf-8").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            identity[k.strip()] = v.strip()
    poids_kg = float(identity.get("Weight", "70").split()[0])

    xls = pd.ExcelFile(excel_file)
    sheet = st.selectbox("Feuille", xls.sheet_names)
    df = xls.parse(sheet).dropna()

    time_col = st.selectbox("Temps", [c for c in df.columns if "Time" in c])
    smo2_col = st.selectbox("SmO₂", [c for c in df.columns if "SmO2" in c])
    power_col = st.selectbox("Puissance", [c for c in df.columns if "Power" in c or "Target" in c])
    hr_col = st.selectbox("Fréquence cardiaque", [c for c in df.columns if "HR" in c or "Fréquence" in c])

    df = df[[time_col, smo2_col, power_col, hr_col]]
    df.columns = ["Time", "SmO2", "Power", "HR"]
    df["SmO2_norm"] = 100 * (df["SmO2"] - df["SmO2"].min()) / (df["SmO2"].max() - df["SmO2"].min())

    s1 = st.slider("S1 (s)", int(df["Time"].min()), int(df["Time"].max()), int(df["Time"].min()) + 200)
    s2 = st.slider("S2 (s)", int(df["Time"].min()), int(df["Time"].max()), int(df["Time"].min()) + 500)
    pma = st.slider("PMA (s)", int(df["Time"].min()), int(df["Time"].max()), int(df["Time"].max()) - 50)

    def get_vals(t):
        row = df.iloc[(df["Time"] - t).abs().argmin()]
        return {
            "power": int(row["Power"]),
            "hr": int(row["HR"]),
            "smo2": round(float(row["SmO2"]), 1),
            "wkg": round(float(row["Power"]) / poids_kg, 2)
        }

    s1_vals = get_vals(s1)
    s2_vals = get_vals(s2)
    pma_vals = get_vals(pma)

    seuils = {"S1": s1_vals, "S2": s2_vals, "PMA": pma_vals}
    zones = [
        {"zone": "Z1", "puissance": f"< {s1_vals['power']} W", "wkg": f"< {s1_vals['wkg']}", "description": "Endurance"},
        {"zone": "Z2", "puissance": f"{s1_vals['power']}–{s2_vals['power']} W", "wkg": f"{s1_vals['wkg']}–{s2_vals['wkg']}", "description": "Tempo"},
        {"zone": "Z3", "puissance": f"> {s2_vals['power']} W", "wkg": f"> {s2_vals['wkg']}", "description": "PMA / I3"},
    ]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Time"], df["SmO2_norm"], color='blue', label="SmO₂ (%)")
    ax.axvline(s1, color='green', linestyle='--', label=f"S1 ({s1_vals['power']} W, {s1_vals['hr']} bpm)")
    ax.axvline(s2, color='red', linestyle='--', label=f"S2 ({s2_vals['power']} W, {s2_vals['hr']} bpm)")
    ax.axvline(pma, color='black', linestyle='--', label=f"PMA ({pma_vals['power']} W, {pma_vals['hr']} bpm)")
    ax.fill_between(df["Time"], 0, 100, where=df["Time"] < s1, color="green", alpha=0.1)
    ax.fill_between(df["Time"], 0, 100, where=(df["Time"] >= s1) & (df["Time"] < s2), color="orange", alpha=0.1)
    ax.fill_between(df["Time"], 0, 100, where=(df["Time"] >= s2) & (df["Time"] < pma), color="red", alpha=0.1)
    ax.fill_between(df["Time"], 0, 100, where=(df["Time"] >= pma), color="skyblue", alpha=0.1)
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("SmO₂ normalisée (%)")
    
legend_elements = [
    mpatches.Patch(color='green', alpha=0.1, label='Z1 : Endurance'),
    mpatches.Patch(color='orange', alpha=0.1, label='Z2 : Tempo'),
    mpatches.Patch(color='red', alpha=0.1, label='Z3 : Haute intensité'),
    mpatches.Patch(color='skyblue', alpha=0.1, label='Réoxygénation'),
]
ax.legend(handles=ax.get_legend_handles_labels()[0] + legend_elements)

    ax.grid(True)
    st.pyplot(fig)

    graph_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(graph_temp.name, dpi=300)

    logo_path = "logo CPO2_06_CMJN.jpg"
    if not os.path.exists(logo_path):
        st.warning("⚠️ Logo 'logo CPO2_06_CMJN.jpg' non trouvé dans le dossier.")
        logo_path = None

    if st.button("📄 Générer le rapport PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            generate_pdf(tmp_pdf.name, identity, seuils, zones, remarques, graph_temp.name, logo_path)
            with open(tmp_pdf.name, "rb") as f:
                st.download_button("📥 Télécharger le PDF", f, file_name=f"{identity.get('Athlete Name', 'rapport')}_CPO2.pdf")
