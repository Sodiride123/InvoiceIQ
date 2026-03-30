#!/bin/bash
# InvoiceIQ — Install dependencies (run once after cloning)
set -e

echo "Installing system packages..."
apt-get update -qq && apt-get install -y -qq tesseract-ocr poppler-utils > /dev/null 2>&1

echo "Installing Python packages..."
pip install -q flask flask-cors pdfplumber pytesseract pdf2image Pillow reportlab requests

echo "Creating data directories..."
cd /workspace/InvoiceIQ
mkdir -p data uploads exports generated processed

echo "Done. Run ./start.sh to start the app."
