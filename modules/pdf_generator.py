# -*- coding: utf-8 -*-
"""
Generador de Remitos Oficiales en PDF con firma digital incrustada.
"""

import os
import io
import datetime
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from modules.app_logging import log_exception

TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_remitos")
os.makedirs(TEMP_DIR, exist_ok=True)

def generate_remito_pdf(remito_header: dict, items: list, signature_image: PILImage = None, evidence_images: list = None) -> str:
    nro_remito = remito_header.get("Nro_Remito", "REMITO")
    safe_nro = str(nro_remito).replace("/", "_").replace("\\", "_")
    pdf_filename = f"{safe_nro}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(TEMP_DIR, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        alignment=TA_LEFT
    )
    style_badge = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=colors.HexColor('#0284C7'),
        alignment=TA_RIGHT
    )
    style_bold_label = ParagraphStyle(
        'BoldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#334155')
    )
    style_normal_val = ParagraphStyle(
        'NormalVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )
    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=TA_CENTER
    )
    style_table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor('#1E293B')
    )
    style_table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor('#1E293B'),
        alignment=TA_CENTER
    )
    style_disclaimer = ParagraphStyle(
        'Disclaimer',
        parent=styles['Italic'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748B'),
        alignment=TA_JUSTIFY
    )

    story = []

    tipo_remito = str(remito_header.get("Tipo", "SALIDA")).upper()
    es_entrada = (tipo_remito == "ENTRADA")

    header_data = [
        [
            Paragraph("<b>DEPARTAMENTO AUTOMOTOR</b><br/><font size=9 color='#64748B'>Área Taller / Control de Inventario</font>", style_title),
            Paragraph(f"<b>REMITO DE {tipo_remito}</b><br/><font size=12 color='#0284C7'>N° {nro_remito}</font>", style_badge)
        ]
    ]
    t_head = Table(header_data, colWidths=[10 * cm, 7 * cm])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_head)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284C7'), spaceBefore=8, spaceAfter=12))

    fecha_hora = remito_header.get("Fecha_Hora", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    responsable = remito_header.get("Responsable_Entrega", "-")
    receptor = remito_header.get("Receptor_Nombre", "-")
    email = remito_header.get("Receptor_Email", "-")
    gerencia = remito_header.get("Gerencia", "-")
    patente = remito_header.get("Patente", "-")
    nro_ot = remito_header.get("Nro_Orden_Taller", "-")

    if es_entrada:
        info_data = [
            [
                Paragraph("<b>Fecha y Hora:</b>", style_bold_label),
                Paragraph(str(fecha_hora), style_normal_val),
                Paragraph("<b>Tipo Movimiento:</b>", style_bold_label),
                Paragraph("INGRESO A TALLER (ENTRADA)", style_normal_val)
            ],
            [
                Paragraph("<b>Responsable de Recepción:</b>", style_bold_label),
                Paragraph(str(responsable), style_normal_val),
                Paragraph("<b>Orden de Taller (OT):</b>", style_bold_label),
                Paragraph(str(nro_ot) if nro_ot else "Sin OT", style_normal_val)
            ],
            [
                Paragraph("<b>Vehículo Asociado:</b>", style_bold_label),
                Paragraph(str(patente) if patente else "Ingreso General a Stock", style_normal_val),
                Paragraph("<b>Área / Destino:</b>", style_bold_label),
                Paragraph("Stock Taller Automotor", style_normal_val)
            ]
        ]
    else:
        info_data = [
            [
                Paragraph("<b>Fecha y Hora:</b>", style_bold_label),
                Paragraph(str(fecha_hora), style_normal_val),
                Paragraph("<b>Receptor / Retira:</b>", style_bold_label),
                Paragraph(str(receptor), style_normal_val)
            ],
            [
                Paragraph("<b>Responsable Entrega:</b>", style_bold_label),
                Paragraph(str(responsable), style_normal_val),
                Paragraph("<b>Email Receptor:</b>", style_bold_label),
                Paragraph(str(email), style_normal_val)
            ],
            [
                Paragraph("<b>Orden de Taller (OT):</b>", style_bold_label),
                Paragraph(str(nro_ot) if nro_ot else "Sin OT", style_normal_val),
                Paragraph("<b>Gerencia / Servicio:</b>", style_bold_label),
                Paragraph(str(gerencia), style_normal_val)
            ],
            [
                Paragraph("<b>Tipo Movimiento:</b>", style_bold_label),
                Paragraph(tipo_remito, style_normal_val),
                Paragraph("<b>Vehículo / Patente:</b>", style_bold_label),
                Paragraph(str(patente) if patente else "-", style_normal_val)
            ]
        ]

    t_info = Table(info_data, colWidths=[3.5 * cm, 5.0 * cm, 3.5 * cm, 5.0 * cm])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 12))

    # Tabla de items
    table_items_data = [
        [
            Paragraph("<b>#</b>", style_table_header),
            Paragraph("<b>Categoría</b>", style_table_header),
            Paragraph("<b>Descripción / Marca / Modelo</b>", style_table_header),
            Paragraph("<b>Cant.</b>", style_table_header),
            Paragraph("<b>N° Serie / Lote / DOT</b>", style_table_header)
        ]
    ]

    for idx, it in enumerate(items, start=1):
        cat = str(it.get("Categoria", ""))
        desc = str(it.get("Descripcion", it.get("Modelo_Detalle", "")))
        marca = str(it.get("Marca", ""))
        full_desc = f"<b>{marca}</b> - {desc}" if marca else desc
        cant = str(it.get("Cantidad", 1))
        serial = it.get("Nro_Serie_Bateria_Neumatico", "-")
        if not serial or serial == "None":
            serial = "-"

        table_items_data.append([
            Paragraph(str(idx), style_table_cell_center),
            Paragraph(cat, style_table_cell),
            Paragraph(full_desc, style_table_cell),
            Paragraph(cant, style_table_cell_center),
            Paragraph(str(serial), style_table_cell)
        ])

    t_items = Table(table_items_data, colWidths=[0.8 * cm, 3.2 * cm, 8.0 * cm, 1.5 * cm, 3.5 * cm])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 10))

    obs = remito_header.get("Observaciones", "")
    if obs:
        obs_table = Table([
            [Paragraph("<b>Observaciones:</b>", style_bold_label)],
            [Paragraph(str(obs), style_normal_val)]
        ], colWidths=[17.0 * cm])
        obs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFBEB')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#FDE68A')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(obs_table)
        story.append(Spacer(1, 10))

    if evidence_images:
        story.append(Paragraph("<b>Fotos de evidencia:</b>", style_bold_label))
        evidence_cells = []
        for image in evidence_images:
            try:
                buffer = io.BytesIO()
                image.thumbnail((500, 500))
                image.save(buffer, format="JPEG", quality=85)
                buffer.seek(0)
                evidence_cells.append(RLImage(buffer, width=7.5 * cm, height=7.5 * cm, kind="proportional"))
            except Exception as exc:
                log_exception("pdf", "No se pudo incorporar una imagen al PDF", exc)
                continue
        for index in range(0, len(evidence_cells), 2):
            row = evidence_cells[index:index + 2]
            if len(row) == 1:
                row.append(Spacer(7.5 * cm, 7.5 * cm))
            story.append(Table([row], colWidths=[8.5 * cm, 8.5 * cm]))
            story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<i>Certifico que la información provista es correcta y los elementos fueron entregados / recibidos de plena conformidad a la fecha y hora indicadas.</i>",
        style_disclaimer
    ))
    story.append(Spacer(1, 10))

    nombre_firmante = responsable if es_entrada else receptor
    rol_firmante = "Responsable de Taller" if es_entrada else "Persona que Recibe"

    sig_cell = Paragraph("__________________________<br/>Firma y Aclaración", style_table_cell_center)
    if signature_image is not None:
        try:
            sig_buf = io.BytesIO()
            signature_image.save(sig_buf, format='PNG')
            sig_buf.seek(0)
            sig_img = RLImage(sig_buf, width=5.5 * cm, height=2.2 * cm)
            sig_cell = [sig_img, Paragraph(f"<b>{nombre_firmante}</b><br/><font size=7 color='#64748B'>Firma Digital Registrada</font>", style_table_cell_center)]
        except Exception:
            pass

    if es_entrada:
        sig_data = [
            [
                Paragraph(f"<b>RECIBIDO EN STOCK POR:</b><br/>{responsable}<br/><font size=7 color='#64748B'>Taller Automotor</font>", style_table_cell_center),
                sig_cell
            ]
        ]
    else:
        sig_data = [
            [
                Paragraph(f"<b>ENTREGADO POR:</b><br/>{responsable}<br/><font size=7 color='#64748B'>Taller Automotor</font>", style_table_cell_center),
                sig_cell
            ]
        ]

    t_sig = Table(sig_data, colWidths=[8.5 * cm, 8.5 * cm])
    t_sig.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_sig)

    doc.build(story)
    return pdf_path

def get_pdf_bytes(pdf_path: str) -> bytes:
    with open(pdf_path, "rb") as f:
        return f.read()
