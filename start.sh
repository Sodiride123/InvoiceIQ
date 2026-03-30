#!/bin/bash
# InvoiceIQ — Start the app via supervisord

APP_DIR=/workspace/invoiceiq
CONF=$APP_DIR/_superninja_startup.conf

# Register with supervisord if not already known
if ! supervisorctl status 7860_python > /dev/null 2>&1; then
  cp "$CONF" /etc/supervisor/conf.d/ 2>/dev/null || true
  supervisorctl reread > /dev/null 2>&1
  supervisorctl update > /dev/null 2>&1
fi

# Start if stopped, restart if already running
STATUS=$(supervisorctl status 7860_python 2>/dev/null | awk '{print $2}')
if [ "$STATUS" = "RUNNING" ]; then
  echo "App already running. Restarting..."
  supervisorctl restart 7860_python > /dev/null 2>&1
else
  supervisorctl start 7860_python > /dev/null 2>&1
fi

echo "InvoiceIQ running on http://0.0.0.0:7860"

# ── Supervisord commands ──
# Start:   supervisorctl start 7860_python
# Stop:    supervisorctl stop 7860_python
# Restart: supervisorctl restart 7860_python
# Status:  supervisorctl status 7860_python
# Logs:    tail -f /var/log/supervisor/7860_python.out.log
