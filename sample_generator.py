"""
InvoiceIQ - Sample Invoice Generator
Creates realistic sample PDF invoices for testing
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER

UPLOADS_DIR = Path(__file__).parent / "uploads"


SAMPLE_INVOICES = [
    {
        "vendor": "Amazon Web Services",
        "address": "410 Terry Ave N, Seattle, WA 98109",
        "invoice_number": "AWS-2024-001847",
        "date": "2024-01-15",
        "due_date": "2024-02-14",
        "payment_terms": "Net 30",
        "items": [
            ("EC2 Instance (t3.medium) - 720 hrs", 1, 33.41),
            ("S3 Storage - 500GB", 1, 11.50),
            ("RDS PostgreSQL - 730 hrs", 1, 48.77),
            ("CloudFront CDN - 1TB transfer", 1, 85.00),
            ("Lambda Invocations - 2M requests", 1, 0.40),
        ],
        "tax_rate": 0.0,
    },
    {
        "vendor": "Adobe Systems Inc",
        "address": "345 Park Avenue, San Jose, CA 95110",
        "invoice_number": "ADB-CC-20240201",
        "date": "2024-02-01",
        "due_date": "2024-02-01",
        "payment_terms": "Due on Receipt",
        "items": [
            ("Creative Cloud All Apps - Annual Plan", 1, 599.88),
            ("Adobe Sign - Business Plan", 1, 299.88),
            ("Adobe Stock - 10 Images/mo", 1, 299.88),
        ],
        "tax_rate": 0.08,
    },
    {
        "vendor": "Delta Air Lines",
        "address": "1030 Delta Blvd, Atlanta, GA 30354",
        "invoice_number": "DL-TKT-4847291",
        "date": "2024-02-12",
        "due_date": "2024-02-12",
        "payment_terms": "Due on Receipt",
        "items": [
            ("Round Trip Flight SFO-NYC (Business)", 1, 1240.00),
            ("Seat Upgrade - Exit Row", 1, 89.00),
            ("Checked Baggage (2 bags)", 2, 35.00),
        ],
        "tax_rate": 0.075,
    },
    {
        "vendor": "Slack Technologies",
        "address": "500 Howard Street, San Francisco, CA 94105",
        "invoice_number": "SLK-PRO-2024-0312",
        "date": "2024-03-01",
        "due_date": "2024-03-31",
        "payment_terms": "Net 30",
        "items": [
            ("Slack Pro - 25 Users x 12 months", 25, 8.75),
        ],
        "tax_rate": 0.0875,
    },
    {
        "vendor": "Marriott International",
        "address": "10400 Fernwood Road, Bethesda, MD 20817",
        "invoice_number": "MRT-RES-8847291",
        "date": "2024-03-15",
        "due_date": "2024-03-15",
        "payment_terms": "Due on Receipt",
        "items": [
            ("Deluxe King Room - 3 nights", 3, 289.00),
            ("Parking - 3 nights", 3, 42.00),
            ("Room Service", 1, 67.50),
            ("Business Center Usage", 1, 25.00),
        ],
        "tax_rate": 0.12,
    },
    {
        "vendor": "Staples Business Advantage",
        "address": "500 Staples Drive, Framingham, MA 01702",
        "invoice_number": "STP-ORD-20240322",
        "date": "2024-03-22",
        "due_date": "2024-04-21",
        "payment_terms": "Net 30",
        "items": [
            ("HP 67XL Black Ink Cartridge (4-pack)", 2, 59.99),
            ("Multipurpose Copy Paper 8.5x11 (10 reams)", 1, 54.99),
            ("Staples Arc Notebook System", 3, 29.99),
            ("Blue Ballpoint Pens (12-pack)", 2, 8.49),
            ("Hanging File Folders (25-pack)", 1, 19.99),
        ],
        "tax_rate": 0.08,
    },
    {
        "vendor": "Google Workspace",
        "address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043",
        "invoice_number": "GWS-2024-Q2-0041",
        "date": "2024-04-01",
        "due_date": "2024-04-30",
        "payment_terms": "Net 30",
        "items": [
            ("Google Workspace Business Plus - 30 Users", 30, 18.00),
            ("Google Cloud Storage - 5TB", 1, 100.00),
        ],
        "tax_rate": 0.0,
    },
    {
        "vendor": "McKinsey & Company",
        "address": "711 Third Avenue, New York, NY 10017",
        "invoice_number": "MCK-2024-CONSULT-089",
        "date": "2024-04-10",
        "due_date": "2024-05-10",
        "payment_terms": "Net 30",
        "items": [
            ("Strategy Consulting - Digital Transformation", 40, 425.00),
            ("Market Analysis Report", 1, 8500.00),
            ("Executive Workshop Facilitation", 2, 3200.00),
        ],
        "tax_rate": 0.0,
    },
    {
        "vendor": "FedEx Corporation",
        "address": "942 South Shady Grove Rd, Memphis, TN 38120",
        "invoice_number": "FDX-2024-04-78234",
        "date": "2024-04-18",
        "due_date": "2024-05-03",
        "payment_terms": "Net 15",
        "items": [
            ("FedEx Priority Overnight - Package 1", 1, 58.95),
            ("FedEx 2Day - Package 2", 1, 24.50),
            ("FedEx Ground - 5 Packages", 5, 12.80),
            ("Residential Delivery Surcharge", 3, 4.95),
        ],
        "tax_rate": 0.0,
    },
    {
        "vendor": "Starbucks Coffee Company",
        "address": "2401 Utah Ave S, Seattle, WA 98134",
        "invoice_number": "SBX-CORP-2024-0428",
        "date": "2024-04-28",
        "due_date": "2024-04-28",
        "payment_terms": "Due on Receipt",
        "items": [
            ("Corporate Catering - Team Meeting (20 people)", 1, 180.00),
            ("Coffee Bar Service - 2 hours", 1, 320.00),
            ("Assorted Pastries & Snacks", 1, 95.00),
        ],
        "tax_rate": 0.095,
    },
    {
        "vendor": "Zoom Video Communications",
        "address": "55 Almaden Blvd, Suite 600, San Jose, CA 95113",
        "invoice_number": "ZM-BIZ-2024-05-0012",
        "date": "2024-05-01",
        "due_date": "2024-05-31",
        "payment_terms": "Net 30",
        "items": [
            ("Zoom Business - 50 Hosts Annual", 50, 16.66),
            ("Zoom Webinar 500 Add-on", 1, 140.00),
            ("Zoom Phone Pro - 20 Users", 20, 15.00),
        ],
        "tax_rate": 0.0,
    },
    {
        "vendor": "Dell Technologies",
        "address": "One Dell Way, Round Rock, TX 78682",
        "invoice_number": "DELL-2024-INV-39847",
        "date": "2024-05-08",
        "due_date": "2024-06-07",
        "payment_terms": "Net 30",
        "items": [
            ("Dell XPS 15 Laptop (Core i9, 32GB RAM)", 2, 2299.99),
            ("Dell UltraSharp 27\" Monitor U2722D", 2, 649.99),
            ("Dell Docking Station WD19S", 2, 249.99),
            ("3-Year ProSupport Plus Warranty", 2, 399.00),
        ],
        "tax_rate": 0.0825,
    },
    {
        "vendor": "Amazon Web Services",
        "address": "410 Terry Ave N, Seattle, WA 98109",
        "invoice_number": "AWS-2024-002341",
        "date": "2024-05-15",
        "due_date": "2024-06-14",
        "payment_terms": "Net 30",
        "items": [
            ("EC2 Instance (t3.medium) - 744 hrs", 1, 33.41),
            ("S3 Storage - 520GB", 1, 11.96),
            ("RDS PostgreSQL - 744 hrs", 1, 48.77),
            ("CloudFront CDN - 1.1TB transfer", 1, 93.50),
            ("Lambda Invocations - 3M requests", 1, 0.60),
        ],
        "tax_rate": 0.0,
    },
    # Duplicate of AWS January invoice (for duplicate detection demo)
    {
        "vendor": "Amazon Web Services",
        "address": "410 Terry Ave N, Seattle, WA 98109",
        "invoice_number": "AWS-2024-001847-DUP",
        "date": "2024-01-15",
        "due_date": "2024-02-14",
        "payment_terms": "Net 30",
        "items": [
            ("EC2 Instance (t3.medium) - 720 hrs", 1, 33.41),
            ("S3 Storage - 500GB", 1, 11.50),
            ("RDS PostgreSQL - 730 hrs", 1, 48.77),
            ("CloudFront CDN - 1TB transfer", 1, 85.00),
            ("Lambda Invocations - 2M requests", 1, 0.40),
        ],
        "tax_rate": 0.0,
    },
    {
        "vendor": "Verizon Business",
        "address": "One Verizon Way, Basking Ridge, NJ 07920",
        "invoice_number": "VZB-2024-06-ACC847291",
        "date": "2024-06-01",
        "due_date": "2024-06-25",
        "payment_terms": "Net 24",
        "items": [
            ("Business Unlimited Plan - 10 Lines", 10, 45.00),
            ("5G Mobile Hotspot Add-on - 10 Lines", 10, 10.00),
            ("International Plan - 2 Lines", 2, 25.00),
            ("Device Protection - 10 Lines", 10, 17.00),
        ],
        "tax_rate": 0.07,
    },
    {
        "vendor": "GitHub Enterprise",
        "address": "88 Colin P Kelly Jr St, San Francisco, CA 94107",
        "invoice_number": "GH-ENT-2024-06-3847",
        "date": "2024-06-01",
        "due_date": "2024-06-30",
        "payment_terms": "Net 30",
        "items": [
            ("GitHub Enterprise Cloud - 40 Users", 40, 21.00),
            ("GitHub Actions - 50,000 additional minutes", 1, 20.00),
            ("GitHub Advanced Security", 40, 49.00),
        ],
        "tax_rate": 0.0,
    },
]


def _create_invoice_pdf(data: dict, output_path: Path):
    """Create a single invoice PDF using ReportLab."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    # Color palette
    primary = colors.HexColor('#1a1a2e')
    accent = colors.HexColor('#4f46e5')
    light_gray = colors.HexColor('#f8f9fa')
    med_gray = colors.HexColor('#e9ecef')
    text_gray = colors.HexColor('#6c757d')

    # ── Header ────────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph(f'<font color="#ffffff" size="20"><b>{data["vendor"]}</b></font>', styles['Normal']),
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

    # ── Info Row ─────────────────────────────────────────────────────────────
    addr_style = ParagraphStyle('addr', parent=styles['Normal'], fontSize=9,
                                 textColor=text_gray, leading=14)
    label_style = ParagraphStyle('label', parent=styles['Normal'], fontSize=8,
                                  textColor=text_gray, spaceAfter=2)
    value_style = ParagraphStyle('value', parent=styles['Normal'], fontSize=10,
                                  textColor=primary, leading=14)
    right_label = ParagraphStyle('rlabel', parent=label_style, alignment=TA_RIGHT)
    right_value = ParagraphStyle('rvalue', parent=value_style, alignment=TA_RIGHT)

    info_data = [[
        Paragraph(f'{data["address"]}', addr_style),
        Table([
            [Paragraph('INVOICE #', right_label),
             Paragraph(f'<b>{data["invoice_number"]}</b>', right_value)],
            [Paragraph('DATE', right_label),
             Paragraph(data["date"], right_value)],
            [Paragraph('DUE DATE', right_label),
             Paragraph(data["due_date"], right_value)],
            [Paragraph('TERMS', right_label),
             Paragraph(data["payment_terms"], right_value)],
        ], colWidths=[1.2 * inch, 1.8 * inch]),
    ]]
    info_table = Table(info_data, colWidths=[4 * inch, 3 * inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.25 * inch))

    # ── Line Items Table ──────────────────────────────────────────────────────
    item_header = [
        Paragraph('<b>DESCRIPTION</b>', ParagraphStyle('th', parent=styles['Normal'],
                   fontSize=9, textColor=colors.white)),
        Paragraph('<b>QTY</b>', ParagraphStyle('thc', parent=styles['Normal'],
                   fontSize=9, textColor=colors.white, alignment=TA_CENTER)),
        Paragraph('<b>UNIT PRICE</b>', ParagraphStyle('thr', parent=styles['Normal'],
                   fontSize=9, textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph('<b>AMOUNT</b>', ParagraphStyle('thr', parent=styles['Normal'],
                   fontSize=9, textColor=colors.white, alignment=TA_RIGHT)),
    ]
    rows = [item_header]

    subtotal = 0.0
    for i, (desc, qty, unit_price) in enumerate(data['items']):
        amount = qty * unit_price
        subtotal += amount
        bg = light_gray if i % 2 == 0 else colors.white
        rows.append([
            Paragraph(desc, ParagraphStyle('td', parent=styles['Normal'], fontSize=9, leading=12)),
            Paragraph(str(qty), ParagraphStyle('tdc', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER)),
            Paragraph(f'${unit_price:,.2f}', ParagraphStyle('tdr', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)),
            Paragraph(f'${amount:,.2f}', ParagraphStyle('tdr', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)),
        ])

    items_table = Table(rows, colWidths=[3.8 * inch, 0.7 * inch, 1.2 * inch, 1.3 * inch])
    item_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), accent),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [light_gray, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, med_gray),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    items_table.setStyle(TableStyle(item_styles))
    story.append(items_table)
    story.append(Spacer(1, 0.2 * inch))

    # ── Totals ────────────────────────────────────────────────────────────────
    tax_amount = subtotal * data['tax_rate']
    total = subtotal + tax_amount

    totals_style = ParagraphStyle('tot', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT)
    totals_label = ParagraphStyle('totl', parent=styles['Normal'], fontSize=10,
                                   textColor=text_gray, alignment=TA_RIGHT)
    total_bold = ParagraphStyle('totb', parent=styles['Normal'], fontSize=13,
                                 textColor=colors.white, alignment=TA_RIGHT)

    totals_data = [
        [Paragraph('Subtotal:', totals_label), Paragraph(f'${subtotal:,.2f}', totals_style)],
        [Paragraph(f'Tax ({data["tax_rate"]*100:.1f}%):', totals_label),
         Paragraph(f'${tax_amount:,.2f}', totals_style)],
    ]
    totals_table = Table(totals_data, colWidths=[2 * inch, 1.3 * inch])
    totals_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    grand_data = [[
        Paragraph('TOTAL DUE:', ParagraphStyle('gtl', parent=styles['Normal'],
                   fontSize=13, textColor=colors.white, alignment=TA_RIGHT)),
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

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=med_gray))
    story.append(Spacer(1, 0.1 * inch))
    footer_style = ParagraphStyle('footer', parent=styles['Normal'], fontSize=8,
                                   textColor=text_gray, alignment=TA_CENTER)
    story.append(Paragraph(
        f'Thank you for your business. Payment due: {data["due_date"]} | Terms: {data["payment_terms"]}',
        footer_style
    ))
    story.append(Paragraph(
        'Please make checks payable to or wire transfer to the account details provided.',
        footer_style
    ))

    doc.build(story)


def generate_all_samples():
    """Generate all sample invoice PDFs."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    generated = []

    for i, inv_data in enumerate(SAMPLE_INVOICES):
        vendor_slug = inv_data['vendor'].lower().replace(' ', '_').replace('&', 'and')[:20]
        date_slug = inv_data['date'].replace('-', '')
        filename = f"invoice_{i+1:02d}_{vendor_slug}_{date_slug}.pdf"
        output_path = UPLOADS_DIR / filename

        if not output_path.exists():
            try:
                _create_invoice_pdf(inv_data, output_path)
                print(f"[Generator] Created: {filename}")
                generated.append(str(output_path))
            except Exception as e:
                print(f"[Generator] Error creating {filename}: {e}")
        else:
            print(f"[Generator] Already exists: {filename}")
            generated.append(str(output_path))

    return generated


if __name__ == "__main__":
    files = generate_all_samples()
    print(f"\n✅ Generated {len(files)} sample invoices in: {UPLOADS_DIR}")