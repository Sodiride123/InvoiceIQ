"""
InvoiceIQ — Invoice PDF Generator
Generates professional PDF invoices from structured data using ReportLab.
Supports multiple templates: professional, modern, minimal.
"""

import os
import uuid
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER

GENERATED_DIR = Path(__file__).parent / "generated"


def _build_professional(data, styles):
    """Professional template — dark header, accent indigo."""
    story = []
    primary = colors.HexColor('#1a1a2e')
    accent = colors.HexColor('#4f46e5')
    light_gray = colors.HexColor('#f8f9fa')
    med_gray = colors.HexColor('#e9ecef')
    text_gray = colors.HexColor('#6c757d')

    # Header
    header_data = [[
        Paragraph(f'<font color="#ffffff" size="20"><b>{data.get("from_name", "Invoice")}</b></font>', styles['Normal']),
        Paragraph('<font color="#ffffff" size="28"><b>INVOICE</b></font>',
                  ParagraphStyle('right', parent=styles['Normal'], alignment=TA_RIGHT))
    ]]
    header_table = Table(header_data, colWidths=[4 * inch, 3 * inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary),
        ('PADDING', (0, 0), (-1, -1), 16),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.2 * inch))

    # From / To + Invoice Info
    addr_style = ParagraphStyle('addr', parent=styles['Normal'], fontSize=9, textColor=text_gray, leading=14)
    label_style = ParagraphStyle('label', parent=styles['Normal'], fontSize=8, textColor=text_gray, spaceAfter=2)
    value_style = ParagraphStyle('value', parent=styles['Normal'], fontSize=10, textColor=primary, leading=14)
    right_label = ParagraphStyle('rlabel', parent=label_style, alignment=TA_RIGHT)
    right_value = ParagraphStyle('rvalue', parent=value_style, alignment=TA_RIGHT)
    section_title = ParagraphStyle('sectitle', parent=styles['Normal'], fontSize=8,
                                    textColor=accent, spaceAfter=4)

    from_addr = data.get('from_address', '')
    to_name = data.get('client_name', '')
    to_addr = data.get('client_address', '')

    left_content = []
    if from_addr:
        left_content.append(Paragraph(f'<b>FROM</b>', section_title))
        left_content.append(Paragraph(f'{data.get("from_name", "")}<br/>{from_addr}', addr_style))
        left_content.append(Spacer(1, 10))
    if to_name:
        left_content.append(Paragraph(f'<b>BILL TO</b>', section_title))
        left_content.append(Paragraph(f'{to_name}<br/>{to_addr}', addr_style))

    left_table = Table([[c] for c in left_content] if left_content else [['']],
                       colWidths=[3.8 * inch])
    left_table.setStyle(TableStyle([('PADDING', (0, 0), (-1, -1), 2)]))

    info_data = [
        [Paragraph('INVOICE #', right_label), Paragraph(f'<b>{data.get("invoice_number", "")}</b>', right_value)],
        [Paragraph('DATE', right_label), Paragraph(data.get('date', ''), right_value)],
        [Paragraph('DUE DATE', right_label), Paragraph(data.get('due_date', ''), right_value)],
        [Paragraph('TERMS', right_label), Paragraph(data.get('payment_terms', 'Net 30'), right_value)],
    ]
    right_table = Table(info_data, colWidths=[1.2 * inch, 1.8 * inch])

    info_outer = Table([[left_table, right_table]], colWidths=[4 * inch, 3 * inch])
    info_outer.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('PADDING', (0, 0), (-1, -1), 4)]))
    story.append(info_outer)
    story.append(Spacer(1, 0.25 * inch))

    # Line Items
    item_header = [
        Paragraph('<b>DESCRIPTION</b>', ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white)),
        Paragraph('<b>QTY</b>', ParagraphStyle('thc', parent=styles['Normal'], fontSize=9, textColor=colors.white, alignment=TA_CENTER)),
        Paragraph('<b>UNIT PRICE</b>', ParagraphStyle('thr', parent=styles['Normal'], fontSize=9, textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph('<b>AMOUNT</b>', ParagraphStyle('thr2', parent=styles['Normal'], fontSize=9, textColor=colors.white, alignment=TA_RIGHT)),
    ]
    rows = [item_header]

    for i, item in enumerate(data.get('items', [])):
        desc = item.get('description', '')
        qty = item.get('quantity', 1)
        price = item.get('unit_price', 0)
        amount = item.get('amount', qty * price)
        qty_str = str(int(qty)) if qty == int(qty) else f'{qty:.2f}'
        rows.append([
            Paragraph(desc, ParagraphStyle('td', parent=styles['Normal'], fontSize=9, leading=12)),
            Paragraph(qty_str, ParagraphStyle('tdc', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER)),
            Paragraph(f'${price:,.2f}', ParagraphStyle('tdr', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)),
            Paragraph(f'${amount:,.2f}', ParagraphStyle('tdr2', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)),
        ])

    items_table = Table(rows, colWidths=[3.8 * inch, 0.7 * inch, 1.2 * inch, 1.3 * inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), accent),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [light_gray, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, med_gray),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.2 * inch))

    # Totals
    subtotal = data.get('subtotal', 0)
    tax_rate = data.get('tax_rate', 0)
    tax_amount = data.get('tax_amount', 0)
    total = data.get('total', 0)

    totals_style = ParagraphStyle('tot', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT)
    totals_label = ParagraphStyle('totl', parent=styles['Normal'], fontSize=10, textColor=text_gray, alignment=TA_RIGHT)
    total_bold = ParagraphStyle('totb', parent=styles['Normal'], fontSize=13, textColor=colors.white, alignment=TA_RIGHT)

    totals_data = [
        [Paragraph('Subtotal:', totals_label), Paragraph(f'${subtotal:,.2f}', totals_style)],
        [Paragraph(f'Tax ({tax_rate*100:.1f}%):', totals_label), Paragraph(f'${tax_amount:,.2f}', totals_style)],
    ]
    totals_table = Table(totals_data, colWidths=[2 * inch, 1.3 * inch])
    totals_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    grand_data = [[
        Paragraph('TOTAL DUE:', ParagraphStyle('gtl', parent=styles['Normal'], fontSize=13, textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph(f'${total:,.2f}', total_bold),
    ]]
    grand_table = Table(grand_data, colWidths=[2 * inch, 1.3 * inch])
    grand_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), accent),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))

    right_col = Table([[totals_table], [Spacer(1, 6)], [grand_table]])
    outer = Table([['', right_col]], colWidths=[4.45 * inch, 3.55 * inch])
    outer.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(outer)
    story.append(Spacer(1, 0.4 * inch))

    # Notes & Footer
    if data.get('notes'):
        story.append(HRFlowable(width="100%", thickness=1, color=med_gray))
        story.append(Spacer(1, 0.1 * inch))
        note_style = ParagraphStyle('note', parent=styles['Normal'], fontSize=9, textColor=text_gray)
        story.append(Paragraph(f'<b>Notes:</b> {data["notes"]}', note_style))
        story.append(Spacer(1, 0.1 * inch))

    story.append(HRFlowable(width="100%", thickness=1, color=med_gray))
    story.append(Spacer(1, 0.1 * inch))
    footer_style = ParagraphStyle('footer', parent=styles['Normal'], fontSize=8, textColor=text_gray, alignment=TA_CENTER)
    story.append(Paragraph(
        f'Payment due: {data.get("due_date", "")} | Terms: {data.get("payment_terms", "Net 30")}',
        footer_style))
    story.append(Paragraph('Generated by InvoiceIQ', footer_style))

    return story


def _build_modern(data, styles):
    """Modern template — emerald-themed, matching the app."""
    story = []
    primary = colors.HexColor('#059669')
    dark = colors.HexColor('#0f172a')
    light_green = colors.HexColor('#ecfdf5')
    med_green = colors.HexColor('#d1fae5')
    text_dark = colors.HexColor('#1e293b')
    text_gray = colors.HexColor('#64748b')

    # Header with gradient-style emerald
    header_data = [[
        Paragraph(f'<font color="#ffffff" size="18"><b>{data.get("from_name", "Invoice")}</b></font>', styles['Normal']),
        Paragraph('<font color="#d1fae5" size="26"><b>INVOICE</b></font>',
                  ParagraphStyle('right', parent=styles['Normal'], alignment=TA_RIGHT))
    ]]
    header_table = Table(header_data, colWidths=[4 * inch, 3 * inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary),
        ('PADDING', (0, 0), (-1, -1), 18),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [8, 8, 0, 0]),
    ]))
    story.append(header_table)

    # Sub-header bar with invoice number and date
    sub_style = ParagraphStyle('sub', parent=styles['Normal'], fontSize=9, textColor=text_dark)
    sub_right = ParagraphStyle('subr', parent=styles['Normal'], fontSize=9, textColor=text_dark, alignment=TA_RIGHT)
    sub_data = [[
        Paragraph(f'<b>#{data.get("invoice_number", "")}</b>  |  {data.get("date", "")}', sub_style),
        Paragraph(f'Due: <b>{data.get("due_date", "")}</b>  |  {data.get("payment_terms", "Net 30")}', sub_right),
    ]]
    sub_table = Table(sub_data, colWidths=[4 * inch, 3 * inch])
    sub_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_green),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 0.25 * inch))

    # From / To cards
    card_title = ParagraphStyle('ctitle', parent=styles['Normal'], fontSize=8, textColor=primary, spaceAfter=4)
    card_body = ParagraphStyle('cbody', parent=styles['Normal'], fontSize=9, textColor=text_dark, leading=14)

    from_content = f'<b>{data.get("from_name", "")}</b>'
    if data.get('from_address'):
        from_content += f'<br/>{data["from_address"]}'
    to_content = f'<b>{data.get("client_name", "")}</b>'
    if data.get('client_address'):
        to_content += f'<br/>{data["client_address"]}'

    cards_data = [[
        Table([
            [Paragraph('FROM', card_title)],
            [Paragraph(from_content, card_body)],
        ], colWidths=[3.3 * inch]),
        Table([
            [Paragraph('BILL TO', card_title)],
            [Paragraph(to_content, card_body)],
        ], colWidths=[3.3 * inch]),
    ]]
    cards_table = Table(cards_data, colWidths=[3.5 * inch, 3.5 * inch])
    cards_table.setStyle(TableStyle([
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#d1fae5')),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor('#d1fae5')),
        ('BACKGROUND', (0, 0), (0, 0), light_green),
        ('BACKGROUND', (1, 0), (1, 0), light_green),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(cards_table)
    story.append(Spacer(1, 0.25 * inch))

    # Line Items
    th_style = ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white)
    th_center = ParagraphStyle('thc', parent=styles['Normal'], fontSize=9, textColor=colors.white, alignment=TA_CENTER)
    th_right = ParagraphStyle('thr', parent=styles['Normal'], fontSize=9, textColor=colors.white, alignment=TA_RIGHT)

    item_header = [
        Paragraph('<b>DESCRIPTION</b>', th_style),
        Paragraph('<b>QTY</b>', th_center),
        Paragraph('<b>RATE</b>', th_right),
        Paragraph('<b>AMOUNT</b>', th_right),
    ]
    rows = [item_header]

    td_style = ParagraphStyle('td', parent=styles['Normal'], fontSize=9, leading=12, textColor=text_dark)
    td_center = ParagraphStyle('tdc', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=text_dark)
    td_right = ParagraphStyle('tdr', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT, textColor=text_dark)

    for item in data.get('items', []):
        qty = item.get('quantity', 1)
        price = item.get('unit_price', 0)
        amount = item.get('amount', qty * price)
        qty_str = str(int(qty)) if qty == int(qty) else f'{qty:.2f}'
        rows.append([
            Paragraph(item.get('description', ''), td_style),
            Paragraph(qty_str, td_center),
            Paragraph(f'${price:,.2f}', td_right),
            Paragraph(f'${amount:,.2f}', td_right),
        ])

    items_table = Table(rows, colWidths=[3.8 * inch, 0.7 * inch, 1.2 * inch, 1.3 * inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_green]),
        ('GRID', (0, 0), (-1, -1), 0.5, med_green),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.2 * inch))

    # Totals
    subtotal = data.get('subtotal', 0)
    tax_rate = data.get('tax_rate', 0)
    tax_amount = data.get('tax_amount', 0)
    total = data.get('total', 0)

    tot_label = ParagraphStyle('totl', parent=styles['Normal'], fontSize=10, textColor=text_gray, alignment=TA_RIGHT)
    tot_val = ParagraphStyle('totv', parent=styles['Normal'], fontSize=10, textColor=text_dark, alignment=TA_RIGHT)
    grand_label = ParagraphStyle('gl', parent=styles['Normal'], fontSize=14, textColor=colors.white, alignment=TA_RIGHT)

    totals_data = [
        [Paragraph('Subtotal:', tot_label), Paragraph(f'${subtotal:,.2f}', tot_val)],
        [Paragraph(f'Tax ({tax_rate*100:.1f}%):', tot_label), Paragraph(f'${tax_amount:,.2f}', tot_val)],
    ]
    totals_table = Table(totals_data, colWidths=[2 * inch, 1.3 * inch])
    totals_table.setStyle(TableStyle([('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))

    grand_data = [[
        Paragraph('<b>TOTAL DUE:</b>', grand_label),
        Paragraph(f'<b>${total:,.2f}</b>', grand_label),
    ]]
    grand_table = Table(grand_data, colWidths=[2 * inch, 1.3 * inch])
    grand_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))

    right_col = Table([[totals_table], [Spacer(1, 6)], [grand_table]])
    outer = Table([['', right_col]], colWidths=[4.45 * inch, 3.55 * inch])
    outer.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(outer)
    story.append(Spacer(1, 0.3 * inch))

    # Notes & Footer
    if data.get('notes'):
        note_style = ParagraphStyle('note', parent=styles['Normal'], fontSize=9, textColor=text_gray)
        story.append(Paragraph(f'<i>{data["notes"]}</i>', note_style))
        story.append(Spacer(1, 0.15 * inch))

    story.append(HRFlowable(width="100%", thickness=1, color=med_green))
    story.append(Spacer(1, 0.08 * inch))
    footer_style = ParagraphStyle('footer', parent=styles['Normal'], fontSize=8, textColor=text_gray, alignment=TA_CENTER)
    story.append(Paragraph('Generated by InvoiceIQ — AI-Powered Invoicing', footer_style))

    return story


def _build_minimal(data, styles):
    """Minimal template — clean black & white, no color."""
    story = []
    black = colors.HexColor('#111827')
    gray = colors.HexColor('#6b7280')
    light_gray = colors.HexColor('#f3f4f6')
    border_gray = colors.HexColor('#d1d5db')

    # Title
    title_style = ParagraphStyle('title', parent=styles['Normal'], fontSize=24, textColor=black, spaceAfter=4)
    story.append(Paragraph('<b>INVOICE</b>', title_style))

    sub_style = ParagraphStyle('sub', parent=styles['Normal'], fontSize=10, textColor=gray)
    story.append(Paragraph(f'#{data.get("invoice_number", "")}', sub_style))
    story.append(Spacer(1, 0.3 * inch))

    # From / To in a simple layout
    label_style = ParagraphStyle('label', parent=styles['Normal'], fontSize=8, textColor=gray, spaceAfter=2)
    body_style = ParagraphStyle('body', parent=styles['Normal'], fontSize=10, textColor=black, leading=14)
    info_style = ParagraphStyle('info', parent=styles['Normal'], fontSize=9, textColor=black, alignment=TA_RIGHT)
    info_label = ParagraphStyle('ilabel', parent=styles['Normal'], fontSize=8, textColor=gray, alignment=TA_RIGHT)

    from_content = f'<b>{data.get("from_name", "")}</b>'
    if data.get('from_address'):
        from_content += f'<br/>{data["from_address"]}'
    to_content = f'<b>{data.get("client_name", "")}</b>'
    if data.get('client_address'):
        to_content += f'<br/>{data["client_address"]}'

    info_block = Table([
        [Paragraph('Date:', info_label), Paragraph(data.get('date', ''), info_style)],
        [Paragraph('Due:', info_label), Paragraph(data.get('due_date', ''), info_style)],
        [Paragraph('Terms:', info_label), Paragraph(data.get('payment_terms', 'Net 30'), info_style)],
    ], colWidths=[0.8 * inch, 1.6 * inch])

    top_data = [[
        Table([
            [Paragraph('From', label_style)],
            [Paragraph(from_content, body_style)],
            [Spacer(1, 12)],
            [Paragraph('Bill To', label_style)],
            [Paragraph(to_content, body_style)],
        ], colWidths=[4 * inch]),
        info_block,
    ]]
    top_table = Table(top_data, colWidths=[4.6 * inch, 2.4 * inch])
    top_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('PADDING', (0, 0), (-1, -1), 2)]))
    story.append(top_table)
    story.append(Spacer(1, 0.3 * inch))

    # Divider
    story.append(HRFlowable(width="100%", thickness=2, color=black))
    story.append(Spacer(1, 0.05 * inch))

    # Line Items
    th_style = ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=gray)
    th_right = ParagraphStyle('thr', parent=styles['Normal'], fontSize=9, textColor=gray, alignment=TA_RIGHT)
    th_center = ParagraphStyle('thc', parent=styles['Normal'], fontSize=9, textColor=gray, alignment=TA_CENTER)
    td_style = ParagraphStyle('td', parent=styles['Normal'], fontSize=9, textColor=black, leading=12)
    td_right = ParagraphStyle('tdr', parent=styles['Normal'], fontSize=9, textColor=black, alignment=TA_RIGHT)
    td_center = ParagraphStyle('tdc', parent=styles['Normal'], fontSize=9, textColor=black, alignment=TA_CENTER)

    rows = [[
        Paragraph('Description', th_style),
        Paragraph('Qty', th_center),
        Paragraph('Rate', th_right),
        Paragraph('Amount', th_right),
    ]]

    for item in data.get('items', []):
        qty = item.get('quantity', 1)
        price = item.get('unit_price', 0)
        amount = item.get('amount', qty * price)
        qty_str = str(int(qty)) if qty == int(qty) else f'{qty:.2f}'
        rows.append([
            Paragraph(item.get('description', ''), td_style),
            Paragraph(qty_str, td_center),
            Paragraph(f'${price:,.2f}', td_right),
            Paragraph(f'${amount:,.2f}', td_right),
        ])

    items_table = Table(rows, colWidths=[3.8 * inch, 0.7 * inch, 1.2 * inch, 1.3 * inch])
    item_styles = [
        ('LINEBELOW', (0, 0), (-1, 0), 1, border_gray),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    # Add bottom border to each row
    for i in range(1, len(rows)):
        item_styles.append(('LINEBELOW', (0, i), (-1, i), 0.5, colors.HexColor('#e5e7eb')))
    items_table.setStyle(TableStyle(item_styles))
    story.append(items_table)
    story.append(Spacer(1, 0.2 * inch))

    # Totals
    subtotal = data.get('subtotal', 0)
    tax_rate = data.get('tax_rate', 0)
    tax_amount = data.get('tax_amount', 0)
    total = data.get('total', 0)

    tot_label = ParagraphStyle('totl', parent=styles['Normal'], fontSize=10, textColor=gray, alignment=TA_RIGHT)
    tot_val = ParagraphStyle('totv', parent=styles['Normal'], fontSize=10, textColor=black, alignment=TA_RIGHT)
    grand_style = ParagraphStyle('grand', parent=styles['Normal'], fontSize=14, textColor=black, alignment=TA_RIGHT)

    totals_data = [
        [Paragraph('Subtotal', tot_label), Paragraph(f'${subtotal:,.2f}', tot_val)],
        [Paragraph(f'Tax ({tax_rate*100:.1f}%)', tot_label), Paragraph(f'${tax_amount:,.2f}', tot_val)],
        [Paragraph('', tot_label), Paragraph('', tot_val)],  # spacing row
        [Paragraph('<b>Total Due</b>', ParagraphStyle('tgl', parent=styles['Normal'], fontSize=13, textColor=black, alignment=TA_RIGHT)),
         Paragraph(f'<b>${total:,.2f}</b>', grand_style)],
    ]
    totals_table = Table(totals_data, colWidths=[2 * inch, 1.3 * inch])
    totals_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (0, 3), (-1, 3), 2, black),
    ]))

    outer = Table([['', totals_table]], colWidths=[4.45 * inch, 3.55 * inch])
    outer.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(outer)
    story.append(Spacer(1, 0.4 * inch))

    # Notes
    if data.get('notes'):
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_gray))
        story.append(Spacer(1, 0.1 * inch))
        note_style = ParagraphStyle('note', parent=styles['Normal'], fontSize=9, textColor=gray)
        story.append(Paragraph(data['notes'], note_style))

    return story


TEMPLATE_BUILDERS = {
    'professional': _build_professional,
    'modern': _build_modern,
    'minimal': _build_minimal,
}


def generate_invoice_pdf(invoice_data, template='professional', output_dir=None):
    """
    Generate a PDF invoice from structured data.

    Args:
        invoice_data: dict with invoice fields (from AI generator or manual)
        template: 'professional', 'modern', or 'minimal'
        output_dir: optional output directory (defaults to GENERATED_DIR)

    Returns:
        str: filepath to generated PDF
    """
    out_dir = Path(output_dir) if output_dir else GENERATED_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    inv_num = invoice_data.get('invoice_number', 'INV').replace('/', '-').replace(' ', '_')
    filename = f"{inv_num}_{uuid.uuid4().hex[:6]}.pdf"
    output_path = out_dir / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    builder = TEMPLATE_BUILDERS.get(template, _build_professional)
    story = builder(invoice_data, styles)
    doc.build(story)

    return str(output_path)
