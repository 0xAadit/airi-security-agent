#!/bin/bash
# Verifier-mirror for fix tasks: agent patch + fresh DB + verifier-owned server restart + hidden-equivalent suite.
set -u
REPO=/mnt/d/Projects/main-stage/security-agents/UniversalAgenticCompetitionPublic
LT=$REPO/local_task
PLOG=/mnt/d/tmp/opencode/bench-logs
export PYTHONPATH="/root/bench-venv/lib/python3.14/site-packages"
export PATH="/usr/local/bin:/usr/bin:/bin"
VPY=/root/bench-venv/bin/python
rm -rf /tmp/remote-agent && mkdir -p /tmp/remote-agent
cp "$REPO/agent/run.sh" "$REPO/agent/local_agent.py" /tmp/remote-agent/
chmod +x /tmp/remote-agent/run.sh
mirror_one() {
  local task=$1 srctask=$2
  echo "=== $task (verifier mirror) ==="
  cd /root
  rm -rf /app /tests /logs/verifier && mkdir -p /app /tests /logs/verifier
  cp -r "$LT/$srctask/environment/app/." /app/
  cp "$LT/$srctask/tests/test_sqli_"*.py "$LT/$srctask/tests/test_regression.py" "$LT/$srctask/tests/conftest.py" /tests/
  cd /tmp/remote-agent
  S=$(date +%s)
  timeout 500 sh ./run.sh "$(cat "$LT/$srctask/instruction.md")" >"$PLOG/$task.agent.log" 2>&1
  echo "agent rc=$? runtime=$(( $(date +%s) - S ))s"
  # --- verifier steps (test.sh:32-99) ---
  pkill -f "uvicorn main:app" 2>/dev/null || true; sleep 1
  su postgres -c "psql -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='appdb';\" >/dev/null 2>&1 || true"
  su postgres -c "dropdb --if-exists appdb >/dev/null 2>&1 || true"
  su postgres -c "createdb appdb -O appuser >/dev/null 2>&1 || true"
  cd /app
  export DATABASE_URL="postgresql://appuser:apppass@localhost:5432/appdb"
  $VPY -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level warning >"$PLOG/$task.uvicorn.log" 2>&1 &
  UPID=$!
  OK=0
  for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/healthz >/dev/null 2>&1; then OK=1; break; fi
    sleep 1
  done
  echo "healthy: $OK"
  if [ "$OK" = "1" ]; then
    DATABASE_URL="$DATABASE_URL" $VPY -m pytest /tests -q 2>&1 | tail -6
  else
    echo "SERVER FAILED TO START"
  fi
  kill $UPID 2>/dev/null || true; wait 2>/dev/null || true
}
mirror_one fixlogin fix-sqli-login
mirror_one fixsearch fix-sqli-search
echo "=== BENCH4 END ==="
