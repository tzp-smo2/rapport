
import streamlit as st
import os
from analyse_smo2_cpo2_reportlab import generate_pdf
import tempfile

st.set_page_config(page_title="Rapport CPO2", layout="centered")

st.title("🧪 Générateur de Rapport CPO2 – SmO₂")

# Upload du fichier .txt
txt_file = st.file_uploader("📄 Charger le fichier .txt du test", type=["txt"])
graph_file = st.file_uploader("📈 Charger le graphique SmO₂ (png)", type=["png", "jpg"])
logo_file = st.file_uploader("🏷️ Charger le logo CPO2", type=["jpg", "png"])

if txt_file and graph_file and logo_file:
    # Lecture fichier txt
    lines = txt_file.getvalue().decode("utf-8").splitlines()
    identity = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(":", 1)
            identity[key.strip()] = value.strip()

    # Données seuils fictives (à remplacer par vos données dynamiques)
    seuils = {
        "S1": {"power": 180, "wkg": 2.5, "hr": 145, "smo2": 38.2},
        "S2": {"power": 240, "wkg": 3.4, "hr": 172, "smo2": 25.7},
        "PMA": {"power": 300, "wkg": 4.2, "hr": 188, "smo2": 19.8}
    }

    # Données zones fictives
    zones = [
        {"zone": "Z1", "puissance": "150-180 W", "wkg": "2.0–2.5", "description": "Endurance fondamentale"},
        {"zone": "Z2", "puissance": "180-240 W", "wkg": "2.5–3.4", "description": "Zone tempo / seuil aérobie"},
        {"zone": "Z3", "puissance": "240-300 W", "wkg": "3.4–4.2", "description": "Zone I3 / PMA"},
    ]

    remarques = "Test réalisé sans incident. Bonne stabilité de la SmO₂ jusqu’au seuil 2. Pente de réoxygénation rapide."

    # Création fichiers temporaires
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf,          tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_graph,          tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_logo:

        tmp_graph.write(graph_file.read())
        tmp_logo.write(logo_file.read())

        # Générer le PDF
        try:
            generate_pdf(tmp_pdf.name, identity, seuils, zones, remarques,
                         graph_path=tmp_graph.name, logo_path=tmp_logo.name)

            with open(tmp_pdf.name, "rb") as f:
                st.download_button("📥 Télécharger le rapport PDF", f, file_name=f"{identity.get('Athlete Name', 'rapport')}_CPO2.pdf")
                st.success("✅ Rapport généré avec succès.")
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du PDF : {e}")
