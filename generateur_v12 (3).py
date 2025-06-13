
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Frame
from reportlab.lib import colors
import ruptures as rpt

def detecter_S1_S2_PMA_ruptures(x, y, n_bkps=3):
    y_smooth = savgol_filter(y, window_length=11, polyorder=2)
    signal = y_smooth.reshape(-1, 1)
    model = rpt.Pelt(model="linear").fit(signal)
    bkps = model.predict(pen=5)
    if len(bkps) > n_bkps:
        bkps = bkps[:n_bkps]
    elif len(bkps) < n_bkps:
        raise ValueError("Pas assez de ruptures détectées.")
    idxs = [0] + bkps
    y_fit = np.zeros_like(y_smooth)
    for i in range(len(idxs)-1):
        start, end = idxs[i], idxs[i+1]
        p = np.polyfit(x[start:end], y_smooth[start:end], 1)
        y_fit[start:end] = np.polyval(p, x[start:end])
    t1, t2, t3 = x[bkps[0]-1], x[bkps[1]-1], x[bkps[2]-1]
    return t1, t2, t3, y_fit

def generer_rapport(xlsx_file, txt_file, logo_path="logo_tzp.png", dossier_sortie="."):
    infos = {}
    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                key, value = line.strip().split(":", 1)
                infos[key.strip()] = value.strip()
    nom_complet = infos.get("Athlete Name", "Nom Inconnu")
    prenom, nom = nom_complet.split()
    date_naissance = infos.get("Date of Birth", "")
    age = infos.get("Age", "")
    taille = infos.get("Height", "")
    poids = infos.get("Weight", "")
    sexe = infos.get("Sex", "")
    activite = infos.get("Workout Activity", "")
    test = infos.get("Workout Name", "")
    protocole = infos.get("Testing Protocol", "")
    capteurs = "Moxy, HRM-Dual, Assioma"
    date_test = infos.get("Workout Date", "").replace("/", "-")

    df = pd.read_excel(xlsx_file, sheet_name="DataAverage")
    col_power = next((c for c in df.columns if "Power" in c or "Target" in c), None)
    col_smo2 = next((c for c in df.columns if "SmO2" in c), None)
    col_hr = next((c for c in df.columns if "HR" in c), None)
    if not all([col_power, col_smo2, col_hr]):
        raise ValueError("Colonnes nécessaires manquantes dans le fichier Excel.")

    df_clean = df[[col_power, col_smo2, col_hr, "Time[s]"]].dropna()
    x = df_clean["Time[s]"].values
    y = df_clean[col_smo2].values
    hr = df_clean[col_hr].values

    S1, S2, PMA, y_modele = detecter_S1_S2_PMA_ruptures(x, y)
    y_lisse = savgol_filter(y, window_length=11, polyorder=2)
    f_hr = interp1d(x, hr, bounds_error=False, fill_value="extrapolate")
    hr_seuil1 = int(f_hr(S1))
    hr_seuil2 = int(f_hr(S2))
    hr_pma = int(f_hr(PMA))
    smo2_pma = int(np.mean(y[(x >= PMA) & (x <= PMA + 5)]))

    graph_path = os.path.join(dossier_sortie, f"graph_{prenom}_{nom}.png")
    plt.figure(figsize=(10/2.54, 6/2.54))
    plt.plot(x, y_lisse, label="SmO₂ lissée", color='orange')
    plt.scatter(x, y, label="Données SmO₂", alpha=0.3)
    plt.plot(x, y_modele, 'r', label="Modèle rupture")
    plt.axvline(x=S1, color='green', linestyle='--', label=f"S1 : {S1:.1f} s")
    plt.axvline(x=S2, color='blue', linestyle='--', label=f"S2 : {S2:.1f} s")
    plt.axvline(x=PMA, color='purple', linestyle='--', label=f"PMA : {PMA:.1f} s")
    plt.xlabel("Temps (s)")
    plt.ylabel("SmO₂ (%)")
    plt.title("SmO₂ vs Temps - Seuils détectés")
    plt.legend()
    plt.tight_layout()
    plt.savefig(graph_path, dpi=300)
    plt.close()

    if not os.path.exists(dossier_sortie):
        os.makedirs(dossier_sortie)
    filename = f"{nom}_{prenom}_{date_test}.pdf"
    filepath = os.path.join(dossier_sortie, filename)
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    margin = 1.5 * cm
    c.drawImage(logo_path, margin, height - 3.5*cm, width=3*cm, height=3*cm)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin + 4*cm, height - 2 * cm, "Rapport de Test SmO₂")
    y_cursor = height - 4.5 * cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y_cursor, "Présentation du coureur")
    c.setFont("Helvetica", 10)
    y_cursor -= 0.6 * cm
    c.drawString(margin, y_cursor, f"Nom : {prenom} {nom} | Naissance : {date_naissance} ({age}) | Sexe : {sexe}")
    y_cursor -= 0.5 * cm
    c.drawString(margin, y_cursor, f"Taille : {taille} | Poids : {poids} | Activité : {activite}")
    y_cursor -= 0.5 * cm
    c.drawString(margin, y_cursor, f"Test : {test} | Protocole : {protocole} | Capteurs : {capteurs}")

    y_cursor -= 1 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y_cursor, "Seuils détectés")
    c.setFont("Helvetica", 10)
    y_cursor -= 0.6 * cm
    c.drawString(margin, y_cursor, f"S1 : {S1:.1f} s | HR : {hr_seuil1} bpm")
    y_cursor -= 0.5 * cm
    c.drawString(margin, y_cursor, f"S2 : {S2:.1f} s | HR : {hr_seuil2} bpm")
    y_cursor -= 0.5 * cm
    c.drawString(margin, y_cursor, f"PMA : {PMA:.1f} s | HR max : {hr_pma} bpm | SmO₂ moy : {smo2_pma}%")

    c.drawImage(graph_path, margin, margin, width=12*cm, height=7*cm)
    c.showPage()
    c.save()
