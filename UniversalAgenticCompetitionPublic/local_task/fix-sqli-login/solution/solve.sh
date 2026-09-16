#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PYEOF'
import pathlib

f = pathlib.Path("/app/routers/auth.py")
src = f.read_text()

vulnerable = (
    "        query = (\n"
    "            f\"SELECT id FROM users \"\n"
    "            f\"WHERE username = '{req.username}' AND password = '{req.password}'\"\n"
    "        )\n"
    "        row = await conn.fetchrow(query)"
)
fixed = (
    "        row = await conn.fetchrow(\n"
    "            \"SELECT id FROM users WHERE username = $1 AND password = $2\",\n"
    "            req.username,\n"
    "            req.password,\n"
    "        )"
)

if vulnerable not in src:
    raise SystemExit("ERROR: vulnerable pattern not found — source may have changed")

f.write_text(src.replace(vulnerable, fixed))
print("Patched /app/routers/auth.py")
PYEOF

cd /app
for _ in $(seq 1 30); do
    if python3 - <<'PYEOF'
import urllib.request
urllib.request.urlopen("http://127.0.0.1:8000/healthz", timeout=1).read()
PYEOF
    then
        break
    fi
    sleep 1
done
pytest tests/ -q
echo "All tests pass."