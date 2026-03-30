"""
InvoiceIQ — AI Invoice Generator
Calls LiteLLM gateway to generate invoices from natural language descriptions.
"""

import json
import os
import re
import uuid
import requests
from datetime import datetime, timedelta


def _load_config():
    """Load AI gateway config from settings files."""
    for path in ['/dev/shm/claude_settings.json', '/root/.claude/settings.json']:
        try:
            with open(path) as f:
                settings = json.load(f)
            env = settings.get('env', {})
            base_url = env.get('ANTHROPIC_BASE_URL', '')
            api_key = env.get('ANTHROPIC_AUTH_TOKEN', '')
            if base_url and api_key:
                return {'base_url': base_url, 'api_key': api_key}
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            continue
    return {
        'base_url': os.environ.get('ANTHROPIC_BASE_URL', ''),
        'api_key': os.environ.get('ANTHROPIC_AUTH_TOKEN', ''),
    }


MODELS = ['claude-sonnet-4-6', 'ninja-cline-complex']

SYSTEM_PROMPT = """You are an invoice generation assistant. Given a natural language description of services, generate a complete, professional invoice as a JSON object.

Rules:
1. Parse the description to identify: client name, services rendered, quantities, rates, and any mentioned tax.
2. Generate professional line item descriptions.
3. Calculate all amounts precisely: amount = quantity * unit_price, subtotal = sum of all item amounts, tax_amount = subtotal * tax_rate, total = subtotal + tax_amount.
4. If no tax rate is mentioned, default tax_rate to 0.
5. If no payment terms are mentioned, default to "Net 30".
6. Generate an invoice number in format INV-YYYY-NNN where YYYY is current year and NNN is a random 3-digit number.
7. Set date to today's date and due_date based on payment terms.
8. If the user mentions their business name, use it in from_name. Otherwise use "Your Business Name" as placeholder.
9. Return ONLY a valid JSON object. No markdown code fences, no explanation, no extra text.

Required JSON schema:
{
  "client_name": "string - the client/customer name",
  "client_address": "string - client address or empty string",
  "from_name": "string - the invoicing business name",
  "from_address": "string - the invoicing business address or empty string",
  "invoice_number": "string - INV-YYYY-NNN format",
  "date": "string - YYYY-MM-DD",
  "due_date": "string - YYYY-MM-DD",
  "payment_terms": "string - e.g. Net 30",
  "items": [
    {
      "description": "string",
      "quantity": "number",
      "unit_price": "number",
      "amount": "number"
    }
  ],
  "subtotal": "number",
  "tax_rate": "number between 0 and 1 (e.g. 0.08 for 8%)",
  "tax_amount": "number",
  "total": "number",
  "notes": "string - professional closing note",
  "currency": "USD"
}"""


def _call_ai(messages, model, config, timeout=90):
    """Call the LiteLLM gateway."""
    url = f"{config['base_url'].rstrip('/')}/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {config['api_key']}",
    }
    payload = {
        'model': model,
        'messages': messages,
        'temperature': 0.3,
        'max_tokens': 4096,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data['choices'][0]['message']['content']


def _parse_json_response(text):
    """Extract JSON from AI response, stripping code fences if present."""
    text = text.strip()
    # Strip markdown code fences
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
    return json.loads(text)


def _validate_and_fix(data, overrides=None):
    """Validate invoice data and recalculate all amounts server-side."""
    overrides = overrides or {}

    # Apply overrides
    if overrides.get('from_name'):
        data['from_name'] = overrides['from_name']
    if overrides.get('from_address'):
        data['from_address'] = overrides['from_address']
    if 'tax_rate' in overrides and overrides['tax_rate'] is not None:
        data['tax_rate'] = float(overrides['tax_rate'])

    # Ensure required fields
    data.setdefault('client_name', 'Client')
    data.setdefault('client_address', '')
    data.setdefault('from_name', 'Your Business Name')
    data.setdefault('from_address', '')
    data.setdefault('invoice_number', f"INV-{datetime.now().year}-{uuid.uuid4().hex[:3].upper()}")
    data.setdefault('date', datetime.now().strftime('%Y-%m-%d'))
    data.setdefault('payment_terms', 'Net 30')
    data.setdefault('notes', 'Thank you for your business.')
    data.setdefault('currency', 'USD')
    data.setdefault('tax_rate', 0.0)

    # Calculate due_date from payment terms if not set
    if not data.get('due_date'):
        terms = data.get('payment_terms', 'Net 30')
        days_match = re.search(r'(\d+)', terms)
        days = int(days_match.group(1)) if days_match else 30
        try:
            base_date = datetime.strptime(data['date'], '%Y-%m-%d')
        except (ValueError, TypeError):
            base_date = datetime.now()
        data['due_date'] = (base_date + timedelta(days=days)).strftime('%Y-%m-%d')

    # Ensure items list
    items = data.get('items', [])
    if not items:
        items = [{'description': 'Services rendered', 'quantity': 1, 'unit_price': 0, 'amount': 0}]

    # Recalculate all amounts
    subtotal = 0.0
    for item in items:
        qty = float(item.get('quantity', 1))
        price = float(item.get('unit_price', 0))
        amount = round(qty * price, 2)
        item['quantity'] = qty
        item['unit_price'] = price
        item['amount'] = amount
        subtotal += amount

    data['items'] = items
    data['subtotal'] = round(subtotal, 2)

    tax_rate = float(data.get('tax_rate', 0))
    # Handle percentage values (e.g., 8 instead of 0.08)
    if tax_rate > 1:
        tax_rate = tax_rate / 100.0
    data['tax_rate'] = round(tax_rate, 4)
    data['tax_amount'] = round(subtotal * tax_rate, 2)
    data['total'] = round(data['subtotal'] + data['tax_amount'], 2)

    return data


def generate_invoice(description, overrides=None):
    """
    Generate an invoice from a natural language description.

    Args:
        description: Natural language description of services
        overrides: Optional dict with from_name, from_address, tax_rate

    Returns:
        dict with invoice data or {"error": "message"}
    """
    if not description or not description.strip():
        return {"error": "Please provide a description of your services."}

    config = _load_config()
    if not config['base_url'] or not config['api_key']:
        return {"error": "AI gateway not configured. Check settings."}

    today = datetime.now().strftime('%Y-%m-%d')
    user_msg = f"Today's date is {today}.\n\nGenerate an invoice for the following:\n{description.strip()}"

    if overrides:
        if overrides.get('from_name'):
            user_msg += f"\n\nInvoice from: {overrides['from_name']}"
        if overrides.get('from_address'):
            user_msg += f"\nAddress: {overrides['from_address']}"
        if overrides.get('tax_rate') is not None:
            user_msg += f"\nTax rate: {float(overrides['tax_rate']) * 100}%"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    last_error = None
    for model in MODELS:
        try:
            raw = _call_ai(messages, model, config, timeout=90)
            data = _parse_json_response(raw)
            return _validate_and_fix(data, overrides)
        except requests.Timeout:
            last_error = f"AI model timed out ({model})"
            continue
        except requests.HTTPError as e:
            last_error = f"AI gateway error: {e.response.status_code}"
            continue
        except (json.JSONDecodeError, KeyError) as e:
            last_error = f"Failed to parse AI response: {str(e)}"
            continue
        except Exception as e:
            last_error = str(e)
            continue

    return {"error": last_error or "Failed to generate invoice. Please try again."}
