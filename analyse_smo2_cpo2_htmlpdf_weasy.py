
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from weasyprint import HTML
import base64

st.set_page_config(layout="wide")
st.title("🧪 Analyse SmO₂ & Rapport PDF HTML – CPO2 (WeasyPrint)")

txt_file = st.file_uploader("📄 Fichier .txt du sportif", type=["txt"])
excel_file = st.file_uploader("📊 Données Excel (.xlsx)", type=["xlsx"])
remarques = st.text_area("🖊️ Remarques du testeur")

if txt_file and excel_file:
    identity = {}
    content = txt_file.read().decode("utf-8").splitlines()
    for line in content:
        if ":" in line:
            key, val = line.split(":", 1)
            identity[key.strip()] = val.strip()

    poids_kg = float(identity.get("Weight", "70").split()[0])

    xls = pd.ExcelFile(excel_file)
    sheet = st.selectbox("Feuille de données", xls.sheet_names)
    df = xls.parse(sheet)

    time_col = st.selectbox("Temps (s)", [col for col in df.columns if "Time" in col])
    smo2_col = st.selectbox("SmO₂", [col for col in df.columns if "SmO2" in col])
    power_col = st.selectbox("Puissance", [col for col in df.columns if "Power" in col or "Target" in col])
    hr_col = st.selectbox("Fréquence cardiaque", [col for col in df.columns if "HR" in col or "Fréquence" in col])

    df = df[[time_col, smo2_col, power_col, hr_col]].dropna()
    df.columns = ["Time", "SmO2", "Power", "HR"]

    smo2_min = df["SmO2"].min()
    smo2_max = df["SmO2"].max()
    df["SmO2_norm"] = 100 * (df["SmO2"] - smo2_min) / (smo2_max - smo2_min)

    s1 = st.slider("Position S1 (s)", int(df["Time"].min()), int(df["Time"].max()), int(df["Time"].min()) + 200)
    s2 = st.slider("Position S2 (s)", int(df["Time"].min()), int(df["Time"].max()), int(df["Time"].min()) + 600)
    pma = st.slider("Position PMA (s)", int(df["Time"].min()), int(df["Time"].max()), int(df["Time"].max()) - 100)

    def get_values_at(time_val):
        row = df.iloc[(df['Time'] - time_val).abs().argmin()]
        return {
            "time": int(row['Time']),
            "power": int(row['Power']),
            "hr": int(row['HR']),
            "smo2": float(row['SmO2']),
            "wkg": round(float(row['Power']) / poids_kg, 2)
        }

    s1_vals = get_values_at(s1)
    s2_vals = get_values_at(s2)
    pma_vals = get_values_at(pma)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Time"], df["SmO2_norm"], label="SmO₂ normalisée (%)", color='blue')
    ax.axhspan(100, 100, color='lightblue', alpha=0.3)
    ax.axhspan(s1_vals["smo2"], 100, color='green', alpha=0.2)
    ax.axhspan(s2_vals["smo2"], s1_vals["smo2"], color='orange', alpha=0.2)
    ax.axhspan(0, s2_vals["smo2"], color='red', alpha=0.2)
    ax.axvline(s1, color='green', linestyle='--', label=f'S1 ({s1_vals["power"]} W, {s1_vals["hr"]} bpm)')
    ax.axvline(s2, color='red', linestyle='--', label=f'S2 ({s2_vals["power"]} W, {s2_vals["hr"]} bpm)')
    ax.axvline(pma, color='black', linestyle='--', label=f'PMA ({pma_vals["power"]} W, {pma_vals["hr"]} bpm)')
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("SmO₂ normalisée (%)")
    ax.grid(True)
    ax.legend(loc="best")
    st.pyplot(fig)

    img_buf = BytesIO()
    fig.savefig(img_buf, format="png")
    img_buf.seek(0)
    graph_b64 = base64.b64encode(img_buf.read()).decode()

    html_report = f'''
    <html><head><meta charset="UTF-8">
    <style>
        body {{ font-family: Arial; margin: 40px; }}
        .header {{ display: flex; align-items: center; }}
        .header h1 {{ font-size: 24px; color: #004080; }}
        .section {{ margin-top: 20px; }}
        .section h2 {{ border-bottom: 2px solid #ccc; color: #004080; }}
        .info-test {{ display: flex; gap: 50px; }}
        .table {{ border-collapse: collapse; width: 100%; }}
        .table th, .table td {{ border: 1px solid #ccc; padding: 8px; }}
        .table th {{ background: #eee; }}
        .remarques {{ background: #f9f9f9; border: 1px dashed #ccc; padding: 10px; }}
    </style>
    </head><body>
    <div class="header">
        <h1>Rapport de Test SmO₂ – CPO2</h1>
    </div>

    <div class="section info-test">
      <div>
        <h2>Informations du sportif</h2>
        <p><strong>Nom :</strong> {identity.get("Athlete Name", "")}</p>
        <p><strong>Sexe :</strong> {identity.get("Sex", "")}</p>
        <p><strong>Âge :</strong> {identity.get("Age", "")}</p>
        <p><strong>Poids :</strong> {identity.get("Weight", "")}</p>
      </div>
      <div>
        <h2>Données du test</h2>
        <p><strong>Date :</strong> {identity.get("Workout Date", "")}</p>
        <p><strong>Nom du test :</strong> {identity.get("Workout Name", "")}</p>
        <p><strong>Durée :</strong> {identity.get("Elapsed Time", "")}</p>
        <p><strong>Protocole :</strong> {identity.get("Testing Protocol", "")}</p>
      </div>
    </div>

    <div class="section">
      <h2>Résultats physiologiques</h2>
      <table class="table">
        <tr><th>Seuil</th><th>Puissance (W)</th><th>W/kg</th><th>FC (bpm)</th><th>SmO₂ (%)</th></tr>
        <tr><td>S1</td><td>{s1_vals["power"]}</td><td>{s1_vals["wkg"]}</td><td>{s1_vals["hr"]}</td><td>{s1_vals["smo2"]:.1f}</td></tr>
        <tr><td>S2</td><td>{s2_vals["power"]}</td><td>{s2_vals["wkg"]}</td><td>{s2_vals["hr"]}</td><td>{s2_vals["smo2"]:.1f}</td></tr>
        <tr><td>PMA</td><td>{pma_vals["power"]}</td><td>{pma_vals["wkg"]}</td><td>{pma_vals["hr"]}</td><td>{pma_vals["smo2"]:.1f}</td></tr>
      </table>
    </div>

    <div class="section">
      <h2>Zones d'entraînement</h2>
      <table class="table">
        <tr><th>Zone</th><th>Puissance</th><th>W/kg</th><th>Description</th></tr>
        <tr><td>Zone 1</td><td>&lt; {s1_vals["power"]}</td><td>&lt; {s1_vals["wkg"]}</td><td>Endurance basse intensité</td></tr>
        <tr><td>Zone 2</td><td>{s1_vals["power"]}–{s2_vals["power"]}</td><td>{s1_vals["wkg"]}–{s2_vals["wkg"]}</td><td>Zone aérobie</td></tr>
        <tr><td>Zone 3</td><td>&gt; {s2_vals["power"]}</td><td>&gt; {s2_vals["wkg"]}</td><td>Haute intensité</td></tr>
      </table>
    </div>

    <div class="section remarques">
      <h2>Remarques</h2>
      <p>{remarques}</p>
    </div>

    <div class="section">
      <h2>Graphique SmO₂</h2>
      <img src="data:image/png;base64,{graph_b64}" />
    </div>
    </body></html>
    '''

    if st.button("📄 Générer le PDF HTML"):
        pdf = HTML(string=html_report).write_pdf()
        st.download_button("💾 Télécharger le PDF", data=pdf, file_name="rapport_CPO2.pdf", mime="application/pdf")
