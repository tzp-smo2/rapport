import streamlit as st
import tempfile
import os
from generateur_v12 import generer_rapport
from PIL import Image

st.set_page_config(page_title="Rapport SmO2", layout="centered")

st.title("📊 Générateur de Rapport SmO₂")
st.markdown("Déposez un fichier **.xlsx** (données test) et un fichier **.txt** (profil coureur).")

# === UPLOAD ===
col1, col2 = st.columns(2)
with col1:
    xlsx_file = st.file_uploader("Fichier Excel (.xlsx)", type="xlsx")
with col2:
    txt_file = st.file_uploader("Fichier Infos (.txt)", type="txt")

# === TRAITEMENT ===
if xlsx_file and txt_file:
    with st.spinner("Analyse en cours..."):

        with tempfile.TemporaryDirectory() as tmpdir:
            logo_path = os.path.join(tmpdir, "logo.png")
            # Place ton vrai logo ici si besoin :
            with open(logo_path, "wb") as f:
                f.write(open("logo_tzp.png", "rb").read())

            # Sauver les fichiers temporairement
            xlsx_path = os.path.join(tmpdir, "donnees.xlsx")
            txt_path = os.path.join(tmpdir, "infos.txt")

            with open(xlsx_path, "wb") as f:
                f.write(xlsx_file.read())
            with open(txt_path, "wb") as f:
                f.write(txt_file.read())

            # Générer le rapport
            output_dir = tmpdir
            generer_rapport(xlsx_path, txt_path, logo_path=logo_path, dossier_sortie=output_dir)

            # Récupérer le nom du fichier PDF généré
            pdf_file = [f for f in os.listdir(output_dir) if f.endswith(".pdf")][0]
            pdf_path = os.path.join(output_dir, pdf_file)

            # Récupérer l’image du graphique
            graph_file = [f for f in os.listdir(output_dir) if f.endswith(".png")][0]
            graph_path = os.path.join(output_dir, graph_file)

            st.success("✅ Rapport généré avec succès !")

            # Affichage graphique SmO2
            st.subheader("📉 Graphique SmO₂ détecté")
            st.image(Image.open(graph_path), use_column_width=True)

            # Téléchargement du PDF
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="📥 Télécharger le rapport PDF",
                data=pdf_bytes,
                file_name=pdf_file,
                mime="application/pdf"
            )