#!/usr/bin/env bash
set -euo pipefail

cat > /app/security_report.json <<'JSON'
{
  "findings": [
    {
      "title": "SQL injection in login endpoint",
      "severity": "critical",
      "category": "sql_injection",
      "location": "routers/auth.py login handler, POST /login",
      "evidence": "The login handler builds a SELECT query with f-strings using req.username and req.password before passing it to conn.fetchrow.",
      "impact": "An attacker can submit a username such as admin'-- or admin' OR '1'='1 to bypass password verification and authenticate as another user.",
      "recommendation": "Use asyncpg parameterized queries with $1 and $2 placeholders instead of interpolating user-controlled values into SQL."
    }
  ]
}
JSON

python3 -m json.tool /app/security_report.json > /tmp/security_report.validated.json
mv /tmp/security_report.validated.json /app/security_report.json

echo "Wrote /app/security_report.json"
