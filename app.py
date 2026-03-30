"""
InvoiceIQ - Flask Backend API
"""

import os
import json
import hashlib
import traceback
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from extractor import extract_invoice, CATEGORY_RULES
from data_manager import (
    load_invoices, add_invoice, delete_invoice, delete_invoices_bulk,
    get_invoice, export_csv, get_monthly_summary, get_dashboard_data,
    save_invoices
)
from ai_generator import generate_invoice
from invoice_pdf_generator import generate_invoice_pdf

# ─── App Config ───────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"
GENERATED_DIR = BASE_DIR / "generated"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'webp'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

app = Flask(__name__,
            static_folder=str(STATIC_DIR),
            template_folder=str(TEMPLATES_DIR))
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
CORS(app)

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(str(TEMPLATES_DIR), 'index.html')


@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "service": "InvoiceIQ"})


@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    """Get all processed invoices."""
    try:
        invoices = load_invoices()
        return jsonify({"success": True, "invoices": invoices, "count": len(invoices)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/invoices/<invoice_id>', methods=['GET'])
def get_single_invoice(invoice_id):
    """Get a single invoice by ID."""
    try:
        invoice = get_invoice(invoice_id)
        if invoice:
            return jsonify({"success": True, "invoice": invoice})
        return jsonify({"success": False, "error": "Invoice not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/invoices/<invoice_id>', methods=['DELETE'])
def remove_invoice(invoice_id):
    """Delete an invoice."""
    try:
        success = delete_invoice(invoice_id)
        if success:
            return jsonify({"success": True, "message": "Invoice deleted"})
        return jsonify({"success": False, "error": "Invoice not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/invoices/bulk-delete', methods=['POST'])
def bulk_delete_invoices():
    """Delete multiple invoices at once."""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return jsonify({"success": False, "error": "No invoice IDs provided"}), 400
        deleted = delete_invoices_bulk(ids)
        return jsonify({
            "success": True,
            "message": f"{deleted} invoice(s) deleted",
            "deleted": deleted,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_invoice():
    """Upload and process one or more invoice files."""
    if 'files' not in request.files:
        return jsonify({"success": False, "error": "No files provided"}), 400

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"success": False, "error": "No files selected"}), 400

    existing_invoices = load_invoices()
    results = []

    for file in files:
        if not file or file.filename == '':
            continue
        if not allowed_file(file.filename):
            results.append({
                "filename": file.filename,
                "success": False,
                "error": f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            })
            continue

        try:
            filename = secure_filename(file.filename)
            # Avoid overwrites
            save_path = UPLOAD_FOLDER / filename
            counter = 1
            while save_path.exists():
                stem = Path(filename).stem
                ext = Path(filename).suffix
                save_path = UPLOAD_FOLDER / f"{stem}_{counter}{ext}"
                counter += 1

            file.save(str(save_path))

            # Extract invoice data
            invoice_data = extract_invoice(str(save_path), existing_invoices)

            if 'error' not in invoice_data:
                add_invoice(invoice_data)
                existing_invoices = load_invoices()  # Refresh for duplicate checking
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "invoice": invoice_data,
                    "is_duplicate": invoice_data.get('is_duplicate', False)
                })
            else:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": invoice_data['error']
                })

        except Exception as e:
            traceback.print_exc()
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })

    success_count = sum(1 for r in results if r['success'])
    return jsonify({
        "success": True,
        "processed": len(results),
        "successful": success_count,
        "failed": len(results) - success_count,
        "results": results
    })


@app.route('/api/load-samples', methods=['POST'])
def load_samples():
    """Generate and process sample invoices."""
    try:
        from sample_generator import generate_all_samples
        sample_files = generate_all_samples()

        existing_invoices = load_invoices()
        processed = []

        for filepath in sample_files:
            try:
                invoice_data = extract_invoice(filepath, existing_invoices)
                if 'error' not in invoice_data:
                    add_invoice(invoice_data)
                    existing_invoices = load_invoices()
                    processed.append({
                        "filename": Path(filepath).name,
                        "success": True,
                        "vendor": invoice_data.get('vendor'),
                        "total": invoice_data.get('total'),
                        "is_duplicate": invoice_data.get('is_duplicate', False)
                    })
                else:
                    processed.append({
                        "filename": Path(filepath).name,
                        "success": False,
                        "error": invoice_data['error']
                    })
            except Exception as e:
                processed.append({
                    "filename": Path(filepath).name,
                    "success": False,
                    "error": str(e)
                })

        return jsonify({
            "success": True,
            "message": f"Processed {len(processed)} sample invoices",
            "results": processed
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/dashboard', methods=['GET'])
def dashboard_data():
    """Get all dashboard data."""
    try:
        data = get_dashboard_data()
        return jsonify({"success": True, **data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/summary', methods=['GET'])
def monthly_summary():
    """Get monthly expense summary."""
    try:
        invoices = load_invoices()
        summary = get_monthly_summary(invoices)
        return jsonify({"success": True, "summary": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/export/csv', methods=['GET'])
def export_to_csv():
    """Export invoices to CSV and return file."""
    try:
        invoices = load_invoices()
        filepath = export_csv(invoices)
        return send_file(
            filepath,
            mimetype='text/csv',
            as_attachment=True,
            download_name=Path(filepath).name
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/export/json', methods=['GET'])
def export_to_json():
    """Export invoices as JSON."""
    try:
        invoices = load_invoices()
        return jsonify({"success": True, "invoices": invoices, "count": len(invoices)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/invoices/<invoice_id>/recategorize', methods=['POST'])
def recategorize(invoice_id):
    """Manually update invoice category."""
    try:
        data = request.get_json()
        new_category = data.get('category', '').strip()
        if not new_category:
            return jsonify({"success": False, "error": "Category required"}), 400

        invoices = load_invoices()
        updated = False
        for inv in invoices:
            if inv.get('id') == invoice_id:
                inv['category'] = new_category
                updated = True
                break

        if updated:
            save_invoices(invoices)
            return jsonify({"success": True, "message": "Category updated"})
        return jsonify({"success": False, "error": "Invoice not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/clear', methods=['POST'])
def clear_all():
    """Clear all invoice data."""
    try:
        save_invoices([])
        return jsonify({"success": True, "message": "All data cleared"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get list of all available categories."""
    cats = list(CATEGORY_RULES.keys()) + ["Miscellaneous"]
    return jsonify({"success": True, "categories": cats})


# ─── AI Invoice Creation ─────────────────────────────────────────────────────

@app.route('/api/create-invoice', methods=['POST'])
def create_invoice():
    """Generate an invoice from a natural language description using AI."""
    try:
        data = request.get_json()
        description = (data.get('description') or '').strip()
        if not description:
            return jsonify({"success": False, "error": "Please provide a description of your services."}), 400

        overrides = {}
        if data.get('from_name'):
            overrides['from_name'] = data['from_name']
        if data.get('from_address'):
            overrides['from_address'] = data['from_address']
        if data.get('tax_rate') is not None and data.get('tax_rate') != '':
            try:
                overrides['tax_rate'] = float(data['tax_rate']) / 100.0
            except (ValueError, TypeError):
                pass

        result = generate_invoice(description, overrides or None)

        if 'error' in result:
            return jsonify({"success": False, "error": result['error']}), 500

        return jsonify({"success": True, "invoice": result})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/create-invoice/pdf', methods=['POST'])
def create_invoice_pdf():
    """Generate a PDF from invoice data and return it for download."""
    try:
        data = request.get_json()
        invoice_data = data.get('invoice', data)
        template = data.get('template', 'professional')

        filepath = generate_invoice_pdf(invoice_data, template=template)

        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"invoice_{invoice_data.get('invoice_number', 'new')}.pdf"
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/create-invoice/save', methods=['POST'])
def save_created_invoice():
    """Save an AI-generated invoice to the data store."""
    try:
        data = request.get_json()
        invoice_data = data.get('invoice', data)

        inv_id = hashlib.md5(
            f"{invoice_data.get('client_name','')}{invoice_data.get('total',0)}{invoice_data.get('date','')}".encode()
        ).hexdigest()[:8].upper()

        stored = {
            "id": inv_id,
            "filename": f"ai_generated_{invoice_data.get('invoice_number', 'new')}.pdf",
            "filepath": "",
            "vendor": invoice_data.get('client_name', 'Unknown'),
            "date": invoice_data.get('date', ''),
            "invoice_number": invoice_data.get('invoice_number', ''),
            "subtotal": float(invoice_data.get('subtotal', 0)),
            "tax": float(invoice_data.get('tax_amount', 0)),
            "total": float(invoice_data.get('total', 0)),
            "payment_terms": invoice_data.get('payment_terms', 'Net 30'),
            "category": "Professional Services",
            "line_items": [
                {"description": item.get('description', ''), "amount": float(item.get('amount', 0))}
                for item in invoice_data.get('items', [])
            ],
            "is_duplicate": False,
            "fingerprint": hashlib.md5(
                f"{invoice_data.get('client_name','')}{invoice_data.get('date','')}{invoice_data.get('total',0)}".encode()
            ).hexdigest(),
            "processed_at": datetime.now().isoformat(),
            "source": "ai_generated",
            "from_name": invoice_data.get('from_name', ''),
            "raw_text_preview": f"AI-generated invoice for {invoice_data.get('client_name', 'client')}",
        }

        add_invoice(stored)
        return jsonify({"success": True, "message": "Invoice saved to library", "invoice": stored})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ─── Static File Serving ──────────────────────────────────────────────────────

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(str(STATIC_DIR), filename)


if __name__ == '__main__':
    print("🚀 InvoiceIQ starting on http://0.0.0.0:7860")
    app.run(host='0.0.0.0', port=7860, debug=False)