"""
InvoiceIQ - Data Manager
Handles storage, retrieval, CSV export, and monthly summaries
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict


DATA_FILE = Path(__file__).parent / "data" / "invoices.json"
EXPORTS_DIR = Path(__file__).parent / "exports"


def load_invoices() -> list:
    """Load all invoices from JSON store."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_invoices(invoices: list):
    """Save invoices to JSON store."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(invoices, f, indent=2, default=str)


def add_invoice(invoice: dict) -> list:
    """Add a new invoice to the store."""
    invoices = load_invoices()
    # Remove existing with same ID if re-processing
    invoices = [inv for inv in invoices if inv.get('id') != invoice.get('id')]
    invoices.append(invoice)
    save_invoices(invoices)
    return invoices


def delete_invoice(invoice_id: str) -> bool:
    """Delete an invoice by ID."""
    invoices = load_invoices()
    new_list = [inv for inv in invoices if inv.get('id') != invoice_id]
    if len(new_list) < len(invoices):
        save_invoices(new_list)
        return True
    return False


def delete_invoices_bulk(invoice_ids: list) -> int:
    """Delete multiple invoices by ID. Returns count of deleted."""
    ids_set = set(invoice_ids)
    invoices = load_invoices()
    new_list = [inv for inv in invoices if inv.get('id') not in ids_set]
    deleted = len(invoices) - len(new_list)
    if deleted > 0:
        save_invoices(new_list)
    return deleted


def get_invoice(invoice_id: str) -> dict:
    """Get a single invoice by ID."""
    invoices = load_invoices()
    for inv in invoices:
        if inv.get('id') == invoice_id:
            return inv
    return None


def export_csv(invoices: list = None, filename: str = None) -> str:
    """Export invoices to CSV file."""
    if invoices is None:
        invoices = load_invoices()

    if not filename:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"invoiceiq_export_{ts}.csv"

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = EXPORTS_DIR / filename

    fields = [
        'id', 'filename', 'vendor', 'date', 'invoice_number',
        'subtotal', 'tax', 'total', 'payment_terms', 'category',
        'is_duplicate', 'processed_at'
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for inv in invoices:
            writer.writerow({k: inv.get(k, '') for k in fields})

    return str(filepath)


def get_monthly_summary(invoices: list = None) -> dict:
    """Generate monthly expense summary."""
    if invoices is None:
        invoices = load_invoices()

    valid = [inv for inv in invoices if not inv.get('is_duplicate') and not inv.get('error')]

    # Monthly totals
    monthly = defaultdict(lambda: {"total": 0.0, "count": 0, "tax": 0.0})
    for inv in valid:
        try:
            dt = datetime.strptime(inv['date'][:10], '%Y-%m-%d')
            key = dt.strftime('%Y-%m')
            monthly[key]["total"] += float(inv.get('total', 0))
            monthly[key]["tax"] += float(inv.get('tax', 0))
            monthly[key]["count"] += 1
        except:
            pass

    # Category totals
    category_totals = defaultdict(float)
    for inv in valid:
        cat = inv.get('category', 'Miscellaneous')
        category_totals[cat] += float(inv.get('total', 0))

    # Vendor totals
    vendor_totals = defaultdict(float)
    for inv in valid:
        vendor = inv.get('vendor', 'Unknown')
        vendor_totals[vendor] += float(inv.get('total', 0))

    # Top vendors
    top_vendors = sorted(vendor_totals.items(), key=lambda x: x[1], reverse=True)[:10]

    # Stats
    totals = [float(inv.get('total', 0)) for inv in valid]
    grand_total = sum(totals)
    avg_invoice = grand_total / len(totals) if totals else 0
    duplicate_count = sum(1 for inv in invoices if inv.get('is_duplicate'))

    return {
        "monthly": dict(monthly),
        "categories": dict(category_totals),
        "top_vendors": top_vendors,
        "stats": {
            "total_invoices": len(invoices),
            "valid_invoices": len(valid),
            "duplicate_count": duplicate_count,
            "grand_total": round(grand_total, 2),
            "total_tax": round(sum(float(inv.get('tax', 0)) for inv in valid), 2),
            "avg_invoice": round(avg_invoice, 2),
            "largest_invoice": round(max(totals) if totals else 0, 2),
        }
    }


def get_dashboard_data() -> dict:
    """Get all data needed for dashboard rendering."""
    invoices = load_invoices()
    summary = get_monthly_summary(invoices)

    # Prepare chart-ready data
    monthly_sorted = sorted(summary['monthly'].items())
    categories_sorted = sorted(summary['categories'].items(), key=lambda x: x[1], reverse=True)

    return {
        "invoices": invoices,
        "summary": summary,
        "chart_data": {
            "monthly_labels": [m[0] for m in monthly_sorted],
            "monthly_totals": [round(m[1]['total'], 2) for m in monthly_sorted],
            "monthly_counts": [m[1]['count'] for m in monthly_sorted],
            "category_labels": [c[0] for c in categories_sorted],
            "category_totals": [round(c[1], 2) for c in categories_sorted],
            "top_vendor_labels": [v[0] for v in summary['top_vendors']],
            "top_vendor_totals": [round(v[1], 2) for v in summary['top_vendors']],
        }
    }