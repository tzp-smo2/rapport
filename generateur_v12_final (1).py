import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Frame
from reportlab.lib import colors


import ruptures as rpt
from scipy.signal import savgol_filter

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




def detecter_S1_S2_3segments(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, np.ndarray]:
    from scipy.signal import savgol_filter
    y_smooth = savgol_filter(y, window_length=11, polyorder=2)

    best_error = float('inf')
    best_t1, best_t2 = None, None
    best_model = None

    n = len(x)
    min_sep = int(n * 0.05)

    for i in range(min_sep, n - 2 * min_sep):
        for j in range(i + min_sep, n - min_sep):
            p1 = np.polyfit(x[:i], y_smooth[:i], 1)
            y1_fit = np.polyval(p1, x[:i])

            p2 = np.polyfit(x[i:j], y_smooth[i:j], 1)
            y2_fit = np.polyval(p2, x[i:j])

            p3 = np.polyfit(x[j:], y_smooth[j:], 1)
            y3_fit = np.polyval(p3, x[j:])

            y_model = np.concatenate([y1_fit, y2_fit, y3_fit])
            error = np.sum((y_smooth - y_model)**2)

            if error < best_error:
                best_error = error
                best_t1 = x[i]
                best_t2 = x[j]
                best_model = y_model

    return best_t1, best_t2, best_model



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

    # Lissage et détection seuils

    # Lissage et détection des ruptures S1, S2, PMA via ruptures
    S1, S2, PMA, y_modele = detecter_S1_S2_PMA_ruptures(x, y)
    y_lisse = savgol_filter(y, window_length=11, polyorder=2)
f_hr = interp1d(x, hr, bounds_error=False, fill_value="extrapolate")
    hr_seuil1 = int(f_hr(S1))
    hr_seuil2 = int(f_hr(S2))

    window = 6
    max_avg = 0
    best_idx = 0
    for i in range(len(x) - window + 1):
        avg = np.mean(x[i:i + window])
        if avg > max_avg:
            max_avg = avg
            best_idx = i
    pma_puissance = int(PMA)
    pma_hr = int(np.max(hr[best_idx:best_idx + window]))
    pma_smo2 = int(np.round(np.mean(y[best_idx:best_idx + window])))

    zones = {
        "Zone 1 (récupération)": f"< {0.85 * S1:.0f} s",
        "Zone 2 (aérobie basse)": f"{0.85 * S1:.0f} - {S1:.0f} s",
        "Zone 3 (aérobie haute)": f"{S1:.0f} - {S2:.0f} s",
        "Zone 4 (seuil anaérobie)": f"{S2:.0f} - {1.10 * S2:.0f} s",
        "Zone 5 (VO2max)": f"> {1.10 * S2:.0f} s"
    }

    hr_zones = {}
    for zone, plage in zones.items():
        try:
            if "-" in plage:
                val1, val2 = [float(s.replace("s", "").strip()) for s in plage.split("-")]
                hr_zones[zone] = f"{int(f_hr(val1))}–{int(f_hr(val2))} bpm"
            elif "<" in plage:
                val = float(plage.replace("<", "").replace("s", "").strip())
                hr_zones[zone] = f"< {int(f_hr(val))} bpm"
            elif ">" in plage:
                val = float(plage.replace(">", "").replace("s", "").strip())
                hr_zones[zone] = f"> {int(f_hr(val))} bpm"
        except:
            hr_zones[zone] = "n/a"

    objectifs = {
        "1": "Repos actif",
        "2": "Endurance de base",
        "3": "Seuil aérobie",
        "4": "Capacité seuil",
        "5": "VO2max"
    }

    data_table = [["Zone", "Temps (s)", "HR estimée", "Objectif"]]
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
    plt.plot(x, y_lisse, label="SmO₂ lissée", color='orange')
    plt.scatter(x, y, label="Données SmO₂", alpha=0.4)
    plt.plot(x, y_modele, 'r', label="Modèle S1")
    plt.axvline(x=S1, color='green', linestyle='--', label=f"S1 : {S1:.1f} s")
    plt.axvline(x=S2, color='blue', linestyle='--', label=f"S2 : {S2:.1f} s")
    plt.xlabel("Temps (s)", fontsize=8)
    plt.ylabel("SmO₂ (%)", fontsize=8)
    plt.title("SmO₂ vs Temps - Seuils détectés", fontsize=9)
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
    c.drawString(margin, current_y, "Seuil 1 (modèle linéaire)")
    c.setFont("Helvetica", 10)
    current_y -= 0.6 * cm
    c.drawString(margin, current_y, f"{S1:.1f} s | SmO₂ : {y_lisse[np.argmin(abs(x - S1))]:.1f}% | HR : {hr_seuil1} bpm")

    current_y -= 1 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, current_y, "Seuil 2 (cassure plancher)")
    c.setFont("Helvetica", 10)
    current_y -= 0.6 * cm
    c.drawString(margin, current_y, f"{S2:.1f} s | SmO₂ : {y_lisse[np.argmin(abs(x - S2))]:.1f}% | HR : {hr_seuil2} bpm")

    current_y -= 1 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, current_y, "PMA")
    c.setFont("Helvetica", 10)
    current_y -= 0.6 * cm
    c.drawString(margin, current_y, f"{pma_puissance} s | HR max : {pma_hr} bpm | SmO₂ moy : {pma_smo2}%")

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