#!/bin/bash
# DB-backed validation for fix tasks (validation env only; never touches agent submission).
set -u
REPO=/mnt/d/Projects/main-stage/security-agents/UniversalAgenticCompetitionPublic
LT=$REPO/local_task
PLOG=/mnt/d/tmp/opencode/bench-logs
export PYTHONPATH="/root/bench-venv/lib/python3.14/site-packages"
export PATH="/usr/local/bin:/usr/bin:/bin"
VPIP=/root/bench-venv/bin/pip
VPY=/root/bench-venv/bin/python
echo "=== setup deps (once) ==="
$VPIP -q install fastapi 'uvicorn[standard]' asyncpg httpx 2>&1 | tail -2
echo "=== setup postgres (once) ==="
if ! command -v psql >/dev/null 2>&1; then apt-get update -qq 2>&1 | tail -1; DEBIAN_FRONTEND=noninteractive apt-get install -y -qq postgresql 2>&1 | tail -2; fi
service postgresql start 2>&1 | tail -1; sleep 2
su postgres -c "psql -c \"CREATE USER appuser WITH PASSWORD 'apppass';\" 2>/dev/null || true"
su postgres -c "psql -c \"CREATE DATABASE appdb OWNER appuser;\" 2>/dev/null || true"
rm -rf /tmp/remote-agent && mkdir -p /tmp/remote-agent
cp "$REPO/agent/run.sh" "$REPO/agent/local_agent.py" /tmp/remote-agent/
chmod +x /tmp/remote-agent/run.sh
python3 -m py_compile /tmp/remote-agent/local_agent.py && echo "agent compiles OK"
run_one() {
  local task=$1 srctask=$2
  echo "=== $task ==="
  cd /root
  rm -rf /app && mkdir -p /app
  cp -r "$LT/$srctask/environment/app/." /app/
  su postgres -c "psql -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='appdb';\" >/dev/null 2>&1 || true"
  su postgres -c "dropdb --if-exists appdb >/dev/null 2>&1 || true"
  su postgres -c "createdb appdb -O appuser >/dev/null 2>&1 || true"
  cd /tmp/remote-agent
  INSTR=$(cat "$LT/$srctask/instruction.md")
  S=$(date +%s)
  timeout 500 sh ./run.sh "$INSTR" >"$PLOG/$task.agent.log" 2>&1
  echo "agent rc=$? runtime=$(( $(date +%s) - S ))s"
  tail -4 "$PLOG/$task.agent.log"
  cd /app
  export DATABASE_URL="postgresql://appuser:apppass@localhost:5432/appdb"
  pkill -f "uvicorn main:app" 2>/dev/null || true; sleep 1
  $VPY -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level warning >"$PLOG/$task.uvicorn.log" 2>&1 &
  UPID=$!
  OK=0
  for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/healthz >/dev/null 2>&1; then OK=1; break; fi
    sleep 1
  done
  echo "server healthy: $OK"
  if [ "$OK" = "1" ]; then
    $VPY -m pytest tests/ -q 2>&1 | tail -5
  fi
  echo "--- payload probes ---"
  if [ "$task" = "fixlogin" ]; then
    echo "valid login: $(curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8000/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"secret123"}')"
    echo "comment bypass: $(curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8000/login -H 'Content-Type: application/json' -d '{"username":"admin'"'"'--","password":"x"}')"
    echo "or bypass: $(curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8000/login -H 'Content-Type: application/json' -d '{"username":"admin'"'"' OR '"'"'1'"'"'='"'"'1","password":"x"}')"
  else
    LEAK=$(curl -s "http://127.0.0.1:8000/search?q=x%27%20UNION%20SELECT%20NULL%2Cusername%2Cpassword%2CNULL%2CNULL%2CNULL%2CNULL%20FROM%20users--")
    echo "union status: $(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8000/search?q=x%27%20UNION%20SELECT%20NULL%2Cusername%2Cpassword%2CNULL%2CNULL%2CNULL%2CNULL%20FROM%20users--")"
    if echo "$LEAK" | grep -q -E 'secret123|alice'; then echo "LEAKED (bad)"; else echo "no leak (good)"; fi
    echo "normal search: $(curl -s -o /dev/null -w '%{http_code}' 'http://127.0.0.1:8000/search?q=timeout')"
  fi
  kill $UPID 2>/dev/null || true; wait 2>/dev/null || true
}
run_one fixlogin fix-sqli-login
run_one fixsearch fix-sqli-search
echo "=== BENCH3 END ==="
