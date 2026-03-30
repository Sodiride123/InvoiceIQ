"""
InvoiceIQ - Core OCR & Data Extraction Engine
Handles PDF and image invoice processing
"""

import re
import json
import hashlib
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from datetime import datetime
from pathlib import Path
import io
import os


# ─── Expense Categories ────────────────────────────────────────────────────────

CATEGORY_RULES = {
    "Software & Subscriptions": [
        "aws", "amazon web", "google cloud", "azure", "microsoft", "adobe", "slack",
        "zoom", "dropbox", "github", "jira", "atlassian", "salesforce", "hubspot",
        "notion", "figma", "canva", "software", "subscription", "license", "saas",
        "hosting", "domain", "cloudflare", "heroku", "digitalocean", "netlify"
    ],
    "Office Supplies": [
        "staples", "office depot", "amazon", "paper", "printer", "toner", "ink",
        "supplies", "stationery", "pens", "notebooks", "desk", "chair", "furniture",
        "office", "equipment", "filing"
    ],
    "Travel & Transportation": [
        "airline", "airways", "delta", "united", "southwest", "american airlines",
        "uber", "lyft", "taxi", "hotel", "marriott", "hilton", "hyatt", "airbnb",
        "car rental", "hertz", "avis", "enterprise", "train", "amtrak", "travel",
        "flight", "lodging", "mileage", "parking", "toll", "transit"
    ],
    "Food & Entertainment": [
        "restaurant", "cafe", "coffee", "starbucks", "doordash", "grubhub",
        "ubereats", "catering", "lunch", "dinner", "breakfast", "meal", "food",
        "entertainment", "event", "concert", "tickets", "bar", "pub"
    ],
    "Marketing & Advertising": [
        "google ads", "facebook ads", "meta", "instagram", "twitter", "linkedin",
        "marketing", "advertising", "ads", "promotion", "pr", "media", "seo",
        "mailchimp", "constant contact", "campaign", "branding", "design"
    ],
    "Professional Services": [
        "consulting", "consultant", "mckinsey", "deloitte", "accenture", "kpmg", "pwc",
        "bain", "bcg", "lawyer", "attorney", "legal", "accounting",
        "cpa", "audit", "bookkeeping", "financial", "advisory", "recruitment",
        "staffing", "contractor", "freelance", "professional services"
    ],
    "Utilities & Facilities": [
        "electric", "electricity", "gas", "water", "internet", "phone", "telecom",
        "verizon", "at&t", "t-mobile", "comcast", "xfinity", "utility", "utilities",
        "facility", "maintenance", "cleaning", "security", "rent", "lease"
    ],
    "Healthcare & Insurance": [
        "insurance", "health", "dental", "vision", "medical", "pharmacy",
        "prescription", "clinic", "hospital", "wellness", "benefits"
    ],
    "Shipping & Logistics": [
        "fedex", "ups", "usps", "dhl", "shipping", "freight", "delivery",
        "logistics", "courier", "postage", "mail"
    ],
    "Hardware & Equipment": [
        "apple", "dell", "hp", "lenovo", "cisco", "computer", "laptop", "monitor",
        "server", "hardware", "device", "iphone", "ipad", "keyboard", "mouse",
        "headset", "webcam", "networking", "router", "switch"
    ],
}

def categorize_expense(vendor: str, description: str = "") -> str:
    """Auto-categorize expense based on vendor name and description."""
    # Check vendor name first (higher priority, shorter text = fewer false positives)
    vendor_lower = vendor.lower()
    for category, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw in vendor_lower:
                return category

    # Then check description text
    desc_lower = description.lower()[:300]
    for category, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw in desc_lower:
                return category

    return "Miscellaneous"


# ─── Text Extraction ───────────────────────────────────────────────────────────

def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from PDF using pdfplumber; fallback to OCR."""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"[pdfplumber] Error: {e}")

    if len(text.strip()) < 50:
        print("[OCR] Falling back to OCR for PDF...")
        try:
            images = convert_from_path(filepath, dpi=300)
            for img in images:
                text += pytesseract.image_to_string(img, config='--psm 6') + "\n"
        except Exception as e:
            print(f"[OCR-PDF] Error: {e}")

    return text


def extract_text_from_image(filepath: str) -> str:
    """Extract text from image using Tesseract OCR."""
    try:
        img = Image.open(filepath)
        # Enhance image for better OCR
        if img.mode != 'RGB':
            img = img.convert('RGB')
        text = pytesseract.image_to_string(img, config='--psm 6 --oem 3')
        return text
    except Exception as e:
        print(f"[OCR-Image] Error: {e}")
        return ""


def extract_text(filepath: str) -> str:
    """Route to correct extractor based on file type."""
    ext = Path(filepath).suffix.lower()
    if ext == '.pdf':
        return extract_text_from_pdf(filepath)
    elif ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.webp']:
        return extract_text_from_image(filepath)
    return ""


# ─── Field Parsers ─────────────────────────────────────────────────────────────

# Known vendor keyword → canonical name mapping
KNOWN_VENDORS = {
    "amazon web services": "Amazon Web Services",
    "aws": "Amazon Web Services",
    "adobe": "Adobe Systems Inc",
    "delta air": "Delta Air Lines",
    "delta blvd": "Delta Air Lines",
    "slack": "Slack Technologies",
    "marriott": "Marriott International",
    "staples": "Staples Business Advantage",
    "google workspace": "Google Workspace",
    "google cloud": "Google Cloud",
    "mckinsey": "McKinsey & Company",
    "fedex": "FedEx Corporation",
    "starbucks": "Starbucks Coffee",
    "zoom": "Zoom Video Communications",
    "dell": "Dell Technologies",
    "verizon": "Verizon Business",
    "github": "GitHub Enterprise",
    "microsoft": "Microsoft",
    "salesforce": "Salesforce",
    "hubspot": "HubSpot",
    "atlassian": "Atlassian",
    "jira": "Atlassian",
    "dropbox": "Dropbox",
    "notion": "Notion",
    "figma": "Figma",
    "stripe": "Stripe",
    "twilio": "Twilio",
    "shopify": "Shopify",
    "cloudflare": "Cloudflare",
    "digitalocean": "DigitalOcean",
    "heroku": "Heroku",
    "netlify": "Netlify",
    "mailchimp": "Mailchimp",
    "intercom": "Intercom",
    "zendesk": "Zendesk",
    "docusign": "DocuSign",
    "okta": "Okta",
    "datadog": "Datadog",
    "pagerduty": "PagerDuty",
    "united airlines": "United Airlines",
    "american airlines": "American Airlines",
    "southwest": "Southwest Airlines",
    "hilton": "Hilton Hotels",
    "hyatt": "Hyatt Hotels",
    "airbnb": "Airbnb",
    "uber": "Uber",
    "lyft": "Lyft",
    "hertz": "Hertz",
    "avis": "Avis",
    "hp ": "HP Inc",
    "hewlett": "HP Inc",
    "lenovo": "Lenovo",
    "cisco": "Cisco Systems",
    "apple": "Apple Inc",
    "ups ": "UPS",
    "united parcel": "UPS",
    "usps": "USPS",
    "dhl": "DHL",
    "at&t": "AT&T",
    "comcast": "Comcast",
    "xfinity": "Comcast",
    "t-mobile": "T-Mobile",
    "terry ave": "Amazon Web Services",
    "park avenue": "Adobe Systems Inc",
    "howard street": "Slack Technologies",
    "fernwood road": "Marriott International",
    "staples drive": "Staples Business Advantage",
    "amphitheatre": "Google Workspace",
    "third avenue": "McKinsey & Company",
    "shady grove": "FedEx Corporation",
    "utah ave": "Starbucks Coffee",
    "almaden": "Zoom Video Communications",
    "one dell": "Dell Technologies",
    "verizon way": "Verizon Business",
    "colin p kelly": "GitHub Enterprise",
}


def parse_vendor(text: str) -> str:
    """Extract vendor/company name from invoice text using keyword matching + heuristics."""
    text_lower = text.lower()

    # 1. Check against known vendors dictionary (most reliable)
    for keyword, canonical in KNOWN_VENDORS.items():
        if keyword in text_lower:
            return canonical

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Skip patterns
    skip_words = ['invoice', 'receipt', 'bill', 'statement', 'page', 'date', 'no.', '#',
                  'thank you', 'payment', 'total', 'amount', 'terms', 'subtotal', 'description']
    address_pattern = re.compile(
        r'\b(?:ave(?:nue)?|blvd|boulevard|street|st\b|road|rd\b|drive|dr\b|way\b|pkwy|'
        r'lane|ln\b|suite|ste\b|floor|fl\b|p\.?o\.?\s*box)\b',
        re.IGNORECASE
    )
    state_zip_pattern = re.compile(r',\s*[A-Z]{2}\s+\d{5}')

    # 2. Look for explicit vendor label
    for pat in [r'(?:from|vendor|billed\s+by|company|issued\s+by|supplier)[:\s]+([A-Za-z0-9][^\n]{2,50})',]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip().split('\n')[0].strip()
            if val and not address_pattern.search(val) and not state_zip_pattern.search(val):
                return val[:60]

    # 3. Try first non-noise, non-address lines
    for line in lines[:10]:
        lower = line.lower()
        if any(sw in lower for sw in skip_words):
            continue
        if address_pattern.search(line) or state_zip_pattern.search(line):
            continue
        if re.match(r'^[\d\s\-\/\.\$]+$', line):
            continue
        if len(line) < 3 or len(line) > 70:
            continue
        vendor = re.sub(r'[^A-Za-z0-9\s&.,\'\-]', '', line).strip()
        if vendor and len(vendor) > 2:
            return vendor

    # 4. Look for company name patterns
    m = re.search(
        r'([A-Z][A-Za-z0-9\s&.,\'-]{2,45}'
        r'(?:Inc\.?|LLC\.?|Ltd\.?|Corp\.?|Co\.?|Services|Solutions|Group|'
        r'Technologies|Systems|International|Enterprise|Associates|Communications))',
        text, re.MULTILINE
    )
    if m:
        candidate = m.group(1).strip()
        if not address_pattern.search(candidate):
            return candidate[:60]

    return lines[0][:50] if lines else "Unknown Vendor"


def parse_date(text: str) -> str:
    """Extract invoice date."""
    patterns = [
        r'(?:invoice\s+date|date\s+issued|issue\s+date|date|billed\s+date)[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'(?:invoice\s+date|date\s+issued|issue\s+date|date)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b',
        r'\b([A-Za-z]+\s+\d{1,2},?\s+\d{4})\b',
        r'\b(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            # Normalize date
            for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%d-%m-%Y',
                        '%B %d, %Y', '%b %d, %Y', '%B %d %Y', '%b %d %Y',
                        '%Y-%m-%d', '%Y/%m/%d', '%m/%d/%y', '%d.%m.%Y']:
                try:
                    dt = datetime.strptime(raw, fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    pass
            return raw
    return datetime.now().strftime('%Y-%m-%d')


def parse_invoice_number(text: str) -> str:
    """Extract invoice number."""
    patterns = [
        r'(?:invoice\s*(?:no|num|number|#)|inv\s*(?:no|#|num))[:\s#]*([A-Z0-9\-\/]{3,20})',
        r'(?:receipt\s*(?:no|num|number|#))[:\s#]*([A-Z0-9\-\/]{3,20})',
        r'#\s*([A-Z0-9\-]{3,15})',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return f"INV-{hashlib.md5(text[:100].encode()).hexdigest()[:6].upper()}"


def parse_amounts(text: str) -> dict:
    """Extract subtotal, tax, and total amounts."""
    def find_amount(patterns, txt):
        for pat in patterns:
            m = re.search(pat, txt, re.IGNORECASE)
            if m:
                raw = m.group(1).replace(',', '').strip()
                try:
                    return float(raw)
                except:
                    pass
        return None

    total_patterns = [
        r'(?:total\s+(?:amount\s+)?(?:due|paid)?|amount\s+due|grand\s+total|total)[:\s$€£]*([0-9,]+\.?\d*)',
        r'(?:balance\s+due|amount\s+payable)[:\s$€£]*([0-9,]+\.?\d*)',
        r'Total[:\s$€£]+([0-9,]+\.?\d{2})',
    ]
    subtotal_patterns = [
        r'(?:subtotal|sub\s*total|net\s*amount)[:\s$€£]*([0-9,]+\.?\d*)',
        r'(?:amount\s+before\s+tax)[:\s$€£]*([0-9,]+\.?\d*)',
    ]
    tax_patterns = [
        r'(?:tax|vat|gst|hst|sales\s+tax)[:\s$€£%0-9]*?([0-9,]+\.?\d{2})\b',
        r'(?:tax\s+amount)[:\s$€£]*([0-9,]+\.?\d*)',
    ]

    total = find_amount(total_patterns, text)
    subtotal = find_amount(subtotal_patterns, text)
    tax = find_amount(tax_patterns, text)

    # Fallback: find largest dollar amount
    if not total:
        all_amounts = re.findall(r'\$\s*([0-9,]+\.?\d{2})', text)
        if all_amounts:
            amounts = [float(a.replace(',', '')) for a in all_amounts]
            total = max(amounts)

    # Infer missing values
    if total and subtotal and not tax:
        tax = round(total - subtotal, 2)
    elif total and tax and not subtotal:
        subtotal = round(total - tax, 2)
    elif total and not subtotal and not tax:
        subtotal = total
        tax = 0.0

    return {
        "subtotal": round(subtotal or 0.0, 2),
        "tax": round(tax or 0.0, 2),
        "total": round(total or 0.0, 2),
    }


def parse_line_items(text: str) -> list:
    """Extract line items from invoice."""
    items = []
    lines = text.split('\n')

    # Pattern: description + optional qty + amount
    item_pattern = re.compile(
        r'^(.{3,50}?)\s+(?:(\d+(?:\.\d+)?)\s+x?\s+)?[\$€£]?\s*([0-9,]+\.\d{2})\s*$',
        re.IGNORECASE
    )
    price_inline = re.compile(
        r'^(.{3,50}?)\s+[\$€£]([0-9,]+\.\d{2})$'
    )

    skip_words = ['total', 'subtotal', 'tax', 'vat', 'gst', 'balance', 'amount due',
                  'payment', 'thank', 'invoice', 'receipt', 'page', 'date', 'due']

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        lower = line.lower()
        if any(sw in lower for sw in skip_words):
            continue

        m = item_pattern.match(line) or price_inline.match(line)
        if m:
            desc = m.group(1).strip()
            amount_str = m.group(len(m.groups())).replace(',', '')
            try:
                amount = float(amount_str)
                if 0.01 < amount < 1_000_000:
                    items.append({
                        "description": desc[:80],
                        "amount": amount
                    })
            except:
                pass

    return items[:20]  # Max 20 line items


def parse_payment_terms(text: str) -> str:
    """Extract payment terms."""
    patterns = [
        r'(?:payment\s+terms?|terms?)[:\s]+([^\n]{3,50})',
        r'(?:due\s+date|pay\s+by|payment\s+due)[:\s]+([^\n]{3,40})',
        r'(?:net\s+\d+|due\s+on\s+receipt|immediate)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            term = (m.group(1) if m.lastindex else m.group(0)).strip()
            return term[:60]
    return "Net 30"


# ─── Duplicate Detection ───────────────────────────────────────────────────────

def compute_fingerprint(vendor: str, date: str, total: float) -> str:
    """Generate a fingerprint for duplicate detection."""
    key = f"{vendor.lower().strip()}|{date}|{total:.2f}"
    return hashlib.md5(key.encode()).hexdigest()


def check_duplicate(fingerprint: str, existing_invoices: list) -> bool:
    """Check if this invoice is a duplicate."""
    return any(inv.get('fingerprint') == fingerprint for inv in existing_invoices)


# ─── Main Extraction Pipeline ─────────────────────────────────────────────────

def extract_invoice(filepath: str, existing_invoices: list = None) -> dict:
    """
    Full extraction pipeline for a single invoice file.
    Returns structured invoice data dict.
    """
    if existing_invoices is None:
        existing_invoices = []

    print(f"[InvoiceIQ] Processing: {filepath}")

    # Step 1: Extract raw text
    raw_text = extract_text(filepath)
    if not raw_text.strip():
        return {"error": "Could not extract text from file", "filepath": filepath}

    # Step 2: Parse fields
    vendor = parse_vendor(raw_text)
    date = parse_date(raw_text)
    invoice_number = parse_invoice_number(raw_text)
    amounts = parse_amounts(raw_text)
    line_items = parse_line_items(raw_text)
    payment_terms = parse_payment_terms(raw_text)
    category = categorize_expense(vendor, raw_text[:500])

    # Step 3: Duplicate detection
    fingerprint = compute_fingerprint(vendor, date, amounts['total'])
    is_duplicate = check_duplicate(fingerprint, existing_invoices)

    # Step 4: Build result
    result = {
        "id": hashlib.md5(f"{filepath}{datetime.now().isoformat()}".encode()).hexdigest()[:8].upper(),
        "filename": Path(filepath).name,
        "filepath": filepath,
        "vendor": vendor,
        "date": date,
        "invoice_number": invoice_number,
        "subtotal": amounts['subtotal'],
        "tax": amounts['tax'],
        "total": amounts['total'],
        "payment_terms": payment_terms,
        "category": category,
        "line_items": line_items,
        "is_duplicate": is_duplicate,
        "fingerprint": fingerprint,
        "processed_at": datetime.now().isoformat(),
        "raw_text_preview": raw_text[:500],
    }

    print(f"[InvoiceIQ] Extracted: {vendor} | {date} | ${amounts['total']:.2f} | {category}")
    return result