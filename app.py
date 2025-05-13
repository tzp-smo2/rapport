import streamlit as st
import tempfile
import os
import io
from PIL import Image
from generateur_v12 import generer_rapport

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
            # Copie du logo local
            logo_path = os.path.join(tmpdir, "logo.png")
            with open("logo_tzp.png", "rb") as lf:
                with open(logo_path, "wb") as out:
                    out.write(lf.read())

            # Enregistrement temporaire des fichiers uploadés
            xlsx_path = os.path.join(tmpdir, "donnees.xlsx")
            txt_path = os.path.join(tmpdir, "infos.txt")
            with open(xlsx_path, "wb") as f:
                f.write(xlsx_file.read())
            with open(txt_path, "wb") as f:
                f.write(txt_file.read())

            # Génération du rapport
            generer_rapport(xlsx_path, txt_path, logo_path=logo_path, dossier_sortie=tmpdir)

            # Chargement des fichiers générés
            pdf_file = [f for f in os.listdir(tmpdir) if f.endswith(".pdf")][0]
            pdf_path = os.path.join(tmpdir, pdf_file)

            graph_file = [f for f in os.listdir(tmpdir) if f.endswith(".png")][0]
            graph_path = os.path.join(tmpdir, graph_file)

            st.success("✅ Rapport généré avec succès !")
            st.subheader("📉 Graphique SmO₂ détecté")

            # Affichage graphique
            try:
                with open(graph_path, "rb") as f:
                    img_bytes = f.read()
                image = Image.open(io.BytesIO(img_bytes))
                st.image(image, use_container_width=True)
            except Exception as e:
                st.warning("Le graphique n'a pas pu être affiché. Mais il est bien dans le PDF.")
                st.text(f"Erreur : {e}")

            # Bouton de téléchargement PDF
            try:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                st.download_button(
                    label="📥 Télécharger le rapport PDF",
                    data=pdf_bytes,
                    file_name=pdf_file,
                    mime="application/pdf"
                )
            except Exception as e:
                st.warning("Le rapport PDF n'a pas pu être chargé.")
                st.text(f"Erreur : {e}")
