
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def generate_pdf(output_path, identity, seuils, zones, remarques, graph_path, logo_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    styleH = styles['Heading1']
    styleH.alignment = TA_CENTER
    styleN = styles['Normal']

    # Titre
    elements.append(Paragraph("Rapport de Test SmO₂ – CPO2", styleH))
    elements.append(Spacer(1, 12))

    # Logo
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, width=4*cm, height=4*cm)
        logo.hAlign = 'RIGHT'
        elements.append(logo)

    # Informations athlète et test
    info_data = [
        [
            Paragraph(f"<b>Nom :</b> {identity.get('Athlete Name', '')}", styleN),
            Paragraph(f"<b>Date :</b> {identity.get('Workout Date', '')}", styleN)
        ],
        [
            Paragraph(f"<b>Sexe :</b> {identity.get('Sex', '')}", styleN),
            Paragraph(f"<b>Nom du test :</b> {identity.get('Workout Name', '')}", styleN)
        ],
        [
            Paragraph(f"<b>Âge :</b> {identity.get('Age', '')}", styleN),
            Paragraph(f"<b>Durée :</b> {identity.get('Elapsed Time', '')}", styleN)
        ],
        [
            Paragraph(f"<b>Poids :</b> {identity.get('Weight', '')}", styleN),
            Paragraph(f"<b>Protocole :</b> {identity.get('Testing Protocol', '')}", styleN)
        ],
    ]
    info_table = Table(info_data, colWidths=[8*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Tableau des résultats aux seuils
    elements.append(Paragraph("Résultats physiologiques", styles['Heading2']))
    seuils_data = [["Seuil", "Puissance (W)", "W/kg", "FC (bpm)", "SmO₂ (%)"]]
    for key in ["S1", "S2", "PMA"]:
        val = seuils.get(key, {})
        seuils_data.append([
            key,
            str(val.get("power", "")),
            str(val.get("wkg", "")),
            str(val.get("hr", "")),
            f'{val.get("smo2", 0):.1f}'
        ])
    seuils_table = Table(seuils_data, hAlign='LEFT')
    seuils_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(seuils_table)
    elements.append(Spacer(1, 20))

    # Tableau des zones
    elements.append(Paragraph("Zones d'entraînement", styles['Heading2']))
    zones_data = [["Zone", "Puissance", "W/kg", "Description"]]
    for z in zones:
        zones_data.append([z["zone"], z["puissance"], z["wkg"], z["description"]])
    zones_table = Table(zones_data, hAlign='LEFT', colWidths=[2*cm, 4*cm, 3*cm, 7*cm])
    zones_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(zones_table)
    elements.append(Spacer(1, 20))

    # Remarques
    elements.append(Paragraph("Remarques", styles['Heading2']))
    remarks_para = Paragraph(f"<i>{remarques}</i>", styleN)
    elements.append(remarks_para)
    elements.append(Spacer(1, 20))

    # Graphique
    if graph_path and os.path.exists(graph_path):
        img = Image(graph_path, width=16*cm, height=6*cm)
        img.hAlign = 'CENTER'
        elements.append(img)

    doc.build(elements)
