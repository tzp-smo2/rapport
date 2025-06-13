
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.lib import colors
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

    # Entête : logo + titre côte à côte
    title = Paragraph("Rapport de Test SmO₂ – CPO2", styleH)
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, width=3.5*cm, height=3.5*cm)
        header = Table([[logo, title]], colWidths=[4*cm, 12*cm])
        header.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        elements.append(header)
    else:
        elements.append(title)

    elements.append(Spacer(1, 20))

    # Identité et infos test
    info_data = [
        [Paragraph(f"<b>Nom :</b> {identity.get('Athlete Name', '')}", styleN),
         Paragraph(f"<b>Date :</b> {identity.get('Workout Date', '')}", styleN)],
        [Paragraph(f"<b>Sexe :</b> {identity.get('Sex', '')}", styleN),
         Paragraph(f"<b>Nom du test :</b> {identity.get('Workout Name', '')}", styleN)],
        [Paragraph(f"<b>Âge :</b> {identity.get('Age', '')}", styleN),
         Paragraph(f"<b>Durée :</b> {identity.get('Elapsed Time', '')}", styleN)],
        [Paragraph(f"<b>Poids :</b> {identity.get('Weight', '')}", styleN),
         Paragraph(f"<b>Protocole :</b> {identity.get('Testing Protocol', '')}", styleN)],
    ]
    info_table = Table(info_data, colWidths=[8*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Résultats physiologiques
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

    # Zones d'entraînement
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
    elements.append(Paragraph(f"<i>{remarques}</i>", styleN))
    elements.append(Spacer(1, 20))

    # Graphique SmO2
    if graph_path and os.path.exists(graph_path):
        img = Image(graph_path, width=16*cm, height=6.5*cm)
        img.hAlign = 'CENTER'
        elements.append(img)

    doc.build(elements)
