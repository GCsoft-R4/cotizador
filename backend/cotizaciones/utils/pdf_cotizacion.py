import os
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, Image, HRFlowable,
)

from .pdf_colors import (
    COLOR_BORDER, COLOR_FOOTER_LINE, COLOR_HEADER_BG,
    COLOR_HEADER_TEXT, COLOR_PRIMARY, COLOR_ROW_ALT,
    COLOR_ROW_HEADER, COLOR_SECONDARY, COLOR_TOTAL_BG,
)
from ..services.documents.pdf_helpers import styles


def _fmt_descuento_pct(val):
    """Formatea el porcentaje de descuento sin ceros sobrantes (18.00 -> '18', 10.50 -> '10.5')."""
    d = Decimal(str(val))
    return str(int(d)) if d == d.to_integral_value() else str(d.normalize())


def _build_elements(cotizacion):
    st = styles()
    elements = []

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        ir = ImageReader(logo_path)
        iw, ih = ir.getSize()
        logo_w = 1.2 * inch
        logo = Image(logo_path, width=logo_w, height=logo_w * (ih / iw))
    else:
        logo = Paragraph('', st['empresa_nombre'])

    empresa_info = Table(
        [[Paragraph('GCinsumos', st['empresa_nombre'])],
         [Paragraph('Servicios InformÃ¡ticos', st['empresa_sub'])],
         [Paragraph('Dilkendein 1278 &nbsp;|&nbsp; Tel: 358-4268768', st['empresa_sub'])]],
        colWidths=[3.5 * inch]
    )
    empresa_info.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    tipo_doc = cotizacion.tipo_documento.upper() if hasattr(cotizacion, 'tipo_documento') else 'COTIZACIÃ“N'

    doc_info = Table(
        [[Paragraph(tipo_doc, st['doc_titulo'])],
         [Paragraph(cotizacion.numero or '', st['doc_numero_blanco'])],
         [Paragraph(f'Fecha: {cotizacion.fecha.strftime("%d/%m/%Y")}', st['doc_numero_blanco'])]],
        colWidths=[2.5 * inch]
    )
    doc_info.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    header_inner = Table(
        [[logo, empresa_info, doc_info]],
        colWidths=[1.4 * inch, 3.5 * inch, 2.5 * inch]
    )
    header_inner.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    header_outer = Table([[header_inner]], colWidths=[7.4 * inch])
    header_outer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_HEADER_BG),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_outer)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph('Datos del cliente', st['seccion']))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=COLOR_BORDER, spaceAfter=6))

    cliente = cotizacion.cliente
    client_data = [
        [Paragraph('Nombre', st['campo_label']),
         Paragraph(cliente.nombre or '-', st['campo_valor']),
         Paragraph('TelÃ©fono', st['campo_label']),
         Paragraph(cliente.telefono or '-', st['campo_valor'])],
        [Paragraph('DirecciÃ³n', st['campo_label']),
         Paragraph(cliente.direccion or 'No especificada', st['campo_valor']),
         Paragraph('Localidad', st['campo_label']),
         Paragraph(cliente.localidad or '-', st['campo_valor'])],
    ]
    client_table = Table(client_data, colWidths=[1.2*inch, 2.4*inch, 1.1*inch, 2.7*inch])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_ROW_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LINEBELOW', (0, 0), (-1, 0), 0.3, COLOR_BORDER),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 14))

    if cotizacion.items.exists():
        elements.append(Paragraph('Detalle de productos', st['seccion']))
        elements.append(HRFlowable(width='100%', thickness=0.5, color=COLOR_BORDER, spaceAfter=6))

        table_data = [[
            Paragraph('Producto', st['tabla_header']),
            Paragraph('Proveedor', st['tabla_header']),
            Paragraph('Cant.', st['tabla_header']),
            Paragraph('Precio Unit.', st['tabla_header']),
            Paragraph('Subtotal', st['tabla_header']),
        ]]

        for i, item in enumerate(cotizacion.items.all()):
            table_data.append([
                Paragraph(item.producto.nombre, st['tabla_celda']),
                Paragraph(item.producto.proveedor.nombre, st['tabla_celda']),
                Paragraph(str(item.cantidad), st['tabla_celda']),
                Paragraph(f'${item.precio_unitario:,.2f}', st['tabla_derecha']),
                Paragraph(f'${item.subtotal:,.2f}', st['tabla_derecha']),
            ])

        descuento_pct = Decimal(str(cotizacion.descuento_porcentaje or 0))

        table_data.append(['', '', '', Paragraph('Subtotal:', st['tabla_derecha']),
                            Paragraph(f'${cotizacion.subtotal_bruto:,.2f}', st['tabla_derecha'])])
        if descuento_pct > 0:
            table_data.append(['', '', '', Paragraph(f'Descuento ({_fmt_descuento_pct(descuento_pct)}%):', st['tabla_derecha']),
                                Paragraph(f'-${cotizacion.monto_descuento:,.2f}', st['tabla_derecha'])])
        table_data.append(['', '', '', Paragraph('TOTAL:', st['tabla_total']),
                            Paragraph(f'${cotizacion.total:,.2f}', st['tabla_total'])])

        last_row = len(table_data) - 1
        subtotal_row = last_row - (2 if descuento_pct > 0 else 1)

        items_table = Table(
            table_data,
            colWidths=[2.3*inch, 1.5*inch, 0.7*inch, 1.3*inch, 1.6*inch],
            repeatRows=1
        )
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_ROW_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_HEADER_TEXT),
            ('TOPPADDING', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
            *[('BACKGROUND', (0, i), (-1, i), colors.white if (i % 2 == 1) else COLOR_ROW_ALT)
              for i in range(1, subtotal_row)],
            ('BOX', (0, 0), (-1, subtotal_row - 1), 0.5, COLOR_BORDER),
            ('INNERGRID', (0, 0), (-1, subtotal_row - 1), 0.3, COLOR_BORDER),
            ('BACKGROUND', (3, subtotal_row), (-1, last_row), COLOR_TOTAL_BG),
            ('LINEABOVE', (3, subtotal_row), (-1, subtotal_row), 1, COLOR_SECONDARY),
            ('LINEBELOW', (3, last_row), (-1, last_row), 1.5, COLOR_PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(items_table)

    if cotizacion.observaciones:
        elements.append(Paragraph('Observaciones', st['obs_titulo']))
        obs_table = Table([[Paragraph(cotizacion.observaciones, st['obs_texto'])]],
                          colWidths=[7.4 * inch])
        obs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_ROW_ALT),
            ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(obs_table)

    elements.append(Spacer(1, 24))
    elements.append(HRFlowable(width='100%', thickness=1, color=COLOR_FOOTER_LINE, spaceAfter=8))
    validez_texto = (
        'Esta cotización tiene una validez de 7 días hábiles.'
        if getattr(cotizacion, 'tipo_documento', '') != 'recibo'
        else None
    )
    if validez_texto:
        elements.append(Paragraph(validez_texto, st['footer_validez']))

    elements.append(Spacer(1, 3))
    elements.append(Paragraph('Paso a paso se llega lejos â€” GCSoft 2025', st['footer_slogan']))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph('GCinsumos &nbsp;|&nbsp; Dilkendein 1278, RÃ­o Cuarto &nbsp;|&nbsp; Tel: 358-4268768 &nbsp;|&nbsp; cristian.e.druetta@gmail.com', st['footer_contacto']))

    return elements


def generar_pdf_buffer(cotizacion):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=30, leftMargin=30,
        topMargin=40, bottomMargin=30
    )
    doc.build(_build_elements(cotizacion))
    buffer.seek(0)
    return buffer


def generar_pdf_cotizacion(cotizacion):
    response = HttpResponse(content_type='application/pdf')

    cliente_nombre = cotizacion.cliente.nombre if cotizacion.cliente and cotizacion.cliente.nombre else 'sin_nombre'
    cliente_slug = cliente_nombre.strip().replace(' ', '_')

    num_doc_raw = (cotizacion.numero or '').replace('Â°', '').strip()

    tipo_doc_attr = getattr(cotizacion, 'tipo_documento', '').lower()

    if 'recibo' in tipo_doc_attr or 'recibo' in num_doc_raw.lower():
        clean_num = num_doc_raw.replace('Recibo_', '').replace('recibo_', '').replace('Recibo', '').replace('recibo', '').strip('_ ')
        filename = f"Recibo_{clean_num}_{cliente_slug}.pdf"

    elif 'cotizacion' in tipo_doc_attr or 'cotizaciÃ³n' in tipo_doc_attr or 'cotizacion' in num_doc_raw.lower() or 'cotizaciÃ³n' in num_doc_raw.lower():
        clean_num = num_doc_raw.replace('Cotizacion_', '').replace('cotizacion_', '').replace('Cotizacion', '').replace('cotizacion', '')
        clean_num = clean_num.replace('CotizaciÃ³n_', '').replace('cotizaciÃ³n_', '').replace('CotizaciÃ³n', '').replace('cotizaciÃ³n', '').strip('_ ')
        filename = f"Cotizacion_{clean_num}_{cliente_slug}.pdf"

    else:
        prefijo = tipo_doc_attr.capitalize() if tipo_doc_attr else 'Documento'
        filename = f"{prefijo}_{num_doc_raw.replace(' ', '_')}_{cliente_slug}.pdf"

    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    buffer = generar_pdf_buffer(cotizacion)
    response.write(buffer.getvalue())
    return response
