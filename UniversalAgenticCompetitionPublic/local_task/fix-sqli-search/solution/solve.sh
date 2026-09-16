#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PYEOF'
import pathlib

f = pathlib.Path("/app/routers/items.py")
src = f.read_text()

vulnerable = (
    "        # VULNERABLE: f-string LIKE concatenation\n"
    "        query = f\"SELECT * FROM items WHERE name LIKE '%{q}%' ORDER BY id ASC\"\n"
    "        rows = await conn.fetch(query)"
)
fixed = (
    "        rows = await conn.fetch(\n"
    "            \"SELECT * FROM items WHERE name LIKE $1 ORDER BY id ASC\",\n"
    "            f\"%{q}%\",\n"
    "        )"
)

if vulnerable not in src:
    raise SystemExit("ERROR: vulnerable pattern not found — source may have changed")

f.write_text(src.replace(vulnerable, fixed))
print("Patched /app/routers/items.py")
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