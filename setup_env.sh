#!/bin/bash
eval "$(cat /root/.claude/settings.json | python3 -c "import sys,json; env=json.load(sys.stdin)['env']; [print(f'export {k}={v}') for k,v in env.items() if k in ('ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL')]")"
