import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from scipy.ndimage import uniform_filter1d
from scipy.signal import savgol_filter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Frame
from reportlab.lib import colors

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
    col_power = next((c for c in df.columns if "Power" in c), None)
    col_smo2 = next((c for c in df.columns if "SmO2" in c), None)
    col_hr = next((c for c in df.columns if "HR" in c), None)

    if not all([col_power, col_smo2, col_hr]):
        raise ValueError("Colonnes nécessaires manquantes dans le fichier Excel.")

    df_clean = df[[col_power, col_smo2, col_hr]].dropna()
    x = df_clean[col_power].values
    y = df_clean[col_smo2].values
    hr = df_clean[col_hr].values

    # === LISSAGE DE LA COURBE SmO2 ===
    y_lisse = savgol_filter(y, window_length=9, polyorder=2)

    # === CALCUL SEUIL 1 PAR MODÈLE LINÉAIRE PAR MORCEAUX SUR COURBE LISSÉE ===
    def piecewise_linear(x, x0, y0, k1, k2):
        return np.where(x < x0, k1*(x - x0) + y0, k2*(x - x0) + y0)

    p0 = [np.median(x), np.median(y_lisse), -0.1, -1.0]
    params1, _ = curve_fit(piecewise_linear, x, y_lisse, p0)
    x0, y0, k1, k2 = params1

    # === SEUIL 2 PAR RUPTURE DE PENTE SUR COURBE LISSEE ===
    pentes = np.gradient(y_lisse, x)
    x_post = x[x > x0]
    pente_post = pentes[x > x0]
    index_seuil2 = np.argmin(np.abs(pente_post))
    x0_2 = x_post[index_seuil2]
    y0_2 = y_lisse[x > x0][index_seuil2]

    f_hr = interp1d(x, hr, bounds_error=False, fill_value="extrapolate")
    hr_seuil1 = int(f_hr(x0))
    hr_seuil2 = int(f_hr(x0_2))

    window = 6
    max_avg = 0
    best_idx = 0
    for i in range(len(x) - window + 1):
        avg = np.mean(x[i:i + window])
        if avg > max_avg:
            max_avg = avg
            best_idx = i
    pma_puissance = int(np.round(max_avg))
    pma_hr = int(np.max(hr[best_idx:best_idx + window]))
    pma_smo2 = int(np.round(np.mean(y[best_idx:best_idx + window])))

    zones = {
        "Zone 1 (récupération)": f"< {0.85 * x0:.0f} W",
        "Zone 2 (aérobie basse)": f"{0.85 * x0:.0f} - {x0:.0f} W",
        "Zone 3 (aérobie haute)": f"{x0:.0f} - {x0_2:.0f} W",
        "Zone 4 (seuil anaérobie)": f"{x0_2:.0f} - {1.10 * x0_2:.0f} W",
        "Zone 5 (VO2max)": f"> {1.10 * x0_2:.0f} W"
    }

    hr_zones = {
        k: f"{int(f_hr(float(v.split()[0])))}–{int(f_hr(float(v.split()[-2])))} bpm"
        if "-" in v else f"< {int(f_hr(float(v.split()[1])))} bpm" if "<" in v else f"> {int(f_hr(float(v.split()[1])))} bpm"
        for k, v in zones.items()
    }

    objectifs = {
        "1": "Repos actif",
        "2": "Endurance de base",
        "3": "Seuil aérobie",
        "4": "Capacité seuil",
        "5": "VO2max"
    }

    data_table = [["Zone", "Puissance (W)", "HR estimée", "Objectif"]]
    for zone, plage in zones.items():
        numero = zone.split()[1][0]
        data_table.append([zone, plage, hr_zones[zone], objectifs[numero]])
    table = Table(data_table, colWidths=[4.2*cm, 4*cm, 4*cm, 4.2*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))

    graph_path = os.path.join(dossier_sortie, f"graph_{prenom}_{nom}.png")
    plt.figure(figsize=(10/2.54, 6/2.54))
    plt.scatter(x, y, label="Données SmO₂", alpha=0.6)
    plt.plot(x, piecewise_linear(x, *params1), 'r', label="Modèle Seuil 1")
    plt.axvline(x=x0, color='green', linestyle='--', label=f"Seuil 1 : {x0:.1f} W")
    plt.axvline(x=x0_2, color='blue', linestyle='--', label=f"Seuil 2 : {x0_2:.1f} W")
    plt.xlabel("Puissance (W)", fontsize=8)
    plt.ylabel("SmO₂ (%)", fontsize=8)
    plt.title("SmO₂ vs Puissance - Seuils détectés", fontsize=9)
    plt.legend(fontsize=7)
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
    usable_width = width - 2 * margin
    current_y = height - margin

    c.drawImage(logo_path, margin, current_y - 3*cm, width=3*cm, height=3*cm)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin + 4*cm, current_y - 1.2 * cm, "Rapport de Test SmO₂")
    current_y -= 3.5 * cm
    c.line(margin, current_y, width - margin, current_y)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, current_y - 0.8*cm, "Présentation du coureur")
    c.setFont("Helvetica", 10)
    current_y -= 1.4 * cm
    c.drawString(margin, current_y, f"Nom : {prenom} {nom} | Naissance : {date_naissance} ({age}) | Sexe : {sexe}")
    current_y -= 0.5 * cm
    c.drawString(margin, current_y, f"Taille : {taille} | Poids : {poids} | Activité : {activite}")
    current_y -= 0.5 * cm
    c.drawString(margin, current_y, f"Test : {test} | Protocole : {protocole} | Capteurs : {capteurs}")

    current_y -= 1 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, current_y, "Seuil 1")
    c.setFont("Helvetica", 10)
    current_y -= 0.6 * cm
    c.drawString(margin, current_y, f"{x0:.1f} W | SmO₂ : {y0:.1f}% | HR : {hr_seuil1} bpm")

    current_y -= 1 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, current_y, "Seuil 2")
    c.setFont("Helvetica", 10)
    current_y -= 0.6 * cm
    c.drawString(margin, current_y, f"{x0_2:.1f} W | SmO₂ : {y0_2:.1f}% | HR : {hr_seuil2} bpm")

    current_y -= 1 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, current_y, "PMA")
    c.setFont("Helvetica", 10)
    current_y -= 0.6 * cm
    c.drawString(margin, current_y, f"{pma_puissance} W | HR max : {pma_hr} bpm | SmO₂ moy : {pma_smo2}%")

    current_y -= 1.2 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, current_y, "Zones d'entraînement recommandées")
    frame = Frame(margin, current_y - 5*cm, usable_width, 5*cm, showBoundary=0)
    frame.addFromList([table], c)

    image_height = 6.5 * cm
    image_width = image_height * (10 / 6)
    c.drawImage(graph_path, margin, margin, width=image_width, height=image_height)
    c.showPage()
    c.save()

    print(f"✅ Rapport généré : {filepath}")
