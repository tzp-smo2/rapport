
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
import os

# Enregistrer une police compatible Unicode
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

def generate_pdf(output_path, identity, seuils, zones, remarques, graph_path, logo_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.0*cm, bottomMargin=1.0*cm)
    elements = []
    styles = getSampleStyleSheet()
    styleH = ParagraphStyle(name='Titre', parent=styles['Heading1'], fontName='DejaVu',
                            alignment=TA_LEFT, fontSize=20, textColor=colors.HexColor('#003366'),
                            spaceAfter=6, leading=22)
    styleN = ParagraphStyle(name='Normal', parent=styles['Normal'], fontName='DejaVu', fontSize=10)
    styleH2 = ParagraphStyle(name='Heading2', parent=styles['Heading2'], fontName='DejaVu', fontSize=12)
    style_bold_center = ParagraphStyle(name='Nom', parent=styles['Normal'], fontName='DejaVu',
                                       alignment=TA_CENTER, fontSize=14, leading=18, textColor=colors.black)

    # Titre + logo
    titre = Paragraph("<b>Rapport de Test SmO2</b>", styleH)
    if logo_path and os.path.exists(logo_path):
        logo_img = ImageReader(logo_path)
        iw, ih = logo_img.getSize()
        target_height = 3.5 * cm
        aspect = iw / ih
        max_logo_width = 10.5 * cm
        logo_width = min(target_height * aspect, max_logo_width)
        logo = Image(logo_path, width=logo_width, height=target_height)
        title_table = Table([[titre, logo]], colWidths=[16*cm * 1/3, 16*cm * 2/3])
        title_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT')
        ]))
    else:
        title_table = Table([[titre]], colWidths=[16*cm])
    elements.append(title_table)
    elements.append(Spacer(1, 6))

    # Encart NOM encadré
    name_box = Table(
        [[Paragraph(f"<b>{identity.get('Athlete Name', '')}</b>", style_bold_center)]],
        colWidths=[16 * cm]
    )
    name_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(name_box)
    elements.append(Spacer(1, 10))

    # Tableau infos athlète
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
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8))

    # Résultats physiologiques
    elements.append(Paragraph("Résultats physiologiques", styleH2))
    seuils_data = [["Seuil", "Puissance (W)", "W/kg", "FC (bpm)", "SmO2 (%)"]]
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
        ('GRID', (0,0), (-1,-1), 0.4, colors.black),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(seuils_table)
    elements.append(Spacer(1, 8))

    # Zones
    elements.append(Paragraph("Zones d'entraînement", styleH2))
    zones_data = [["Zone", "Puissance", "W/kg", "Description"]]
    for z in zones:
        zones_data.append([z["zone"], z["puissance"], z["wkg"], z["description"]])
    zones_table = Table(zones_data, hAlign='LEFT', colWidths=[2*cm, 4*cm, 3*cm, 7*cm])
    zones_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.4, colors.black),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(zones_table)
    elements.append(Spacer(1, 8))

    # Remarques
    elements.append(Paragraph("Remarques", styleH2))
    remarks_para = Paragraph(f"<i>{remarques}</i>", styleN)
    elements.append(remarks_para)
    elements.append(Spacer(1, 8))

    # Graphique centré agrandi
    if graph_path and os.path.exists(graph_path):
        img = Image(graph_path, width=17*cm, height=7*cm)
        img.hAlign = 'CENTER'
        elements.append(img)

    doc.build(elements)
