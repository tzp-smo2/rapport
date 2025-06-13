
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

st.set_page_config(layout="wide")
st.title("🧪 Analyse SmO₂ & Rapport PDF – CPO2 (v2 structurée)")

txt_file = st.file_uploader("📄 Importer le fichier .txt du sportif", type=["txt"])
identity = {}

if txt_file:
    content = txt_file.read().decode("utf-8").splitlines()
    for line in content:
        if ":" in line:
            key, val = line.split(":", 1)
            identity[key.strip()] = val.strip()

uploaded_file = st.file_uploader("📂 Importer un fichier Excel (.xlsx)", type=["xlsx"])
if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet = st.selectbox("Choisir la feuille de données", xls.sheet_names)
    df = xls.parse(sheet)

    time_col = st.selectbox("Colonne Temps (s)", [col for col in df.columns if "Time" in col])
    smo2_col = st.selectbox("Colonne SmO₂ (%)", [col for col in df.columns if "SmO2" in col])
    power_col = st.selectbox("Colonne Puissance (W)", [col for col in df.columns if "Power" in col or "Target" in col])
    hr_col = st.selectbox("Colonne Fréquence cardiaque (bpm)", [col for col in df.columns if "HR" in col or "Fréquence" in col])

    df = df[[time_col, smo2_col, power_col, hr_col]].dropna()
    df.columns = ['Time', 'SmO2', 'Power', 'HR']

    smo2_min = df['SmO2'].min()
    smo2_max = df['SmO2'].max()
    df['SmO2_norm'] = 100 * (df['SmO2'] - smo2_min) / (smo2_max - smo2_min)

    early_phase = df[df['Time'] <= 120]
    smo2_start_max = early_phase['SmO2'].max()
    smo2_start_max_norm = 100 * (smo2_start_max - smo2_min) / (smo2_max - smo2_min)

    st.subheader("📊 Courbe normalisée de la SmO₂")
    s1 = st.slider("Position de S1 (s)", int(df['Time'].min()), int(df['Time'].max()), int(df['Time'].min()) + 200)
    s2 = st.slider("Position de S2 (s)", int(df['Time'].min()), int(df['Time'].max()), int(df['Time'].min()) + 600)
    pma = st.slider("Position de la PMA (s)", int(df['Time'].min()), int(df['Time'].max()), int(df['Time'].max()) - 100)

    def get_values_at(time_val):
        row = df.iloc[(df['Time'] - time_val).abs().argmin()]
        return row['Time'], row['Power'], row['HR'], row['SmO2'], row['SmO2_norm']

    s1_vals = get_values_at(s1)
    s2_vals = get_values_at(s2)
    pma_vals = get_values_at(pma)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['Time'], df['SmO2_norm'], label='SmO₂ normalisée (%)', color='blue')
    ax.axvline(s1, color='green', linestyle='--')
    ax.axvline(s2, color='red', linestyle='--')
    ax.axvline(pma, color='black', linestyle='--')
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("SmO₂ normalisée (%)")
    ax.set_title("SmO₂ – Zones d'intensité ajustées dynamiquement")
    ax.grid(True)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(fig)

    summary_df = pd.DataFrame({
        'Temps (s)': [s1_vals[0], s2_vals[0], pma_vals[0]],
        'Puissance (W)': [s1_vals[1], s2_vals[1], pma_vals[1]],
        'Fréquence cardiaque (bpm)': [s1_vals[2], s2_vals[2], pma_vals[2]],
        'SmO₂ (%)': [s1_vals[3], s2_vals[3], pma_vals[3]],
    }, index=['Seuil 1', 'Seuil 2', 'PMA'])

    st.dataframe(summary_df)

    remarque = st.text_area("🖊️ Remarques du testeur")

    def create_pdf(buffer, identity, summary_df, remarque, fig):
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Logo
        try:
            c.drawImage("logo CPO2_06_CMJN.jpg", 40, height - 90, width=80, preserveAspectRatio=True)
        except:
            pass

        # Titre
        c.setFont("Helvetica-Bold", 16)
        c.drawString(150, height - 60, "Rapport de Test SmO₂ – CPO2")

        # Infos identité
        c.setFont("Helvetica-Bold", 10)
        y = height - 110
        c.drawString(40, y, "Informations du sportif :")
        c.setFont("Helvetica", 9)
        for field in ["Athlete Name", "Date of Birth", "Age", "Sex", "Height", "Weight"]:
            y -= 12
            c.drawString(50, y, f"{field}: {identity.get(field, '')}")

        y -= 20
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "Données du test :")
        c.setFont("Helvetica", 9)
        for field in ["Workout Name", "Workout Date", "Elapsed Time", "Testing Protocol"]:
            y -= 12
            c.drawString(50, y, f"{field}: {identity.get(field, '')}")

        # Graphique
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        c.drawImage(ImageReader(img_buffer), 40, 250, width=260, height=160)

        # Résultats à droite
        c.setFont("Helvetica-Bold", 10)
        c.drawString(320, 410, "Résultats physiologiques :")
        c.setFont("Helvetica", 9)
        y_r = 390
        for idx, row in summary_df.iterrows():
            c.drawString(320, y_r, f"{idx} : {int(row['Puissance (W)'])} W | {int(row['Fréquence cardiaque (bpm)'])} bpm | SmO₂ : {row['SmO₂ (%)']:.1f}%")
            y_r -= 14

        # Zones d'entraînement
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 210, "Zones d'entraînement estimées :")
        c.setFont("Helvetica", 9)
        s1w, s2w = summary_df.loc['Seuil 1', 'Puissance (W)'], summary_df.loc['Seuil 2', 'Puissance (W)']
        zones = [
            ("Zone 1", f"< {int(s1w)} W", "Endurance faible intensité"),
            ("Zone 2", f"{int(s1w)}–{int(s2w)} W", "Zone aérobie"),
            ("Zone 3", f"> {int(s2w)} W", "Haute intensité")
        ]
        y_z = 190
        for z in zones:
            c.drawString(50, y_z, f"{z[0]} : {z[1]} – {z[2]}")
            y_z -= 12

        # Bloc remarques
        c.setFillColor(colors.lightgrey)
        c.rect(310, 200, 250, 80, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(320, 270, "Remarques :")
        c.setFont("Helvetica", 9)
        y_m = 255
        for line in remarque.splitlines():
            c.drawString(320, y_m, line)
            y_m -= 12

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    if st.button("📄 Générer le rapport PDF structuré"):
        pdf_buffer = BytesIO()
        buffer = create_pdf(pdf_buffer, identity, summary_df, remarque, fig)
        nom_fichier = identity.get("Athlete Name", "rapport") + "_CPO2.pdf"
        st.download_button("💾 Télécharger le PDF structuré", data=buffer, file_name=nom_fichier, mime="application/pdf")
