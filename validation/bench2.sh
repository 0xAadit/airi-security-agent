#!/bin/bash
# Self-contained validation run: venv + shim + agent + verifiers, logs persist on /mnt/d.
set -u
REPO=/mnt/d/Projects/main-stage/security-agents/UniversalAgenticCompetitionPublic
LT=$REPO/local_task
PLOG=/mnt/d/tmp/opencode/bench-logs
mkdir -p "$PLOG" /logs/verifier
# persistent venv (ext4, survives WSL shutdown)
if [ ! -x /root/bench-venv/bin/python ]; then
  python3 -m venv /root/bench-venv
  /root/bench-venv/bin/pip -q install pytest
fi
export PYTHONPATH="/root/bench-venv/lib/python3.14/site-packages"
export PATH="/usr/local/bin:/usr/bin:/bin"
echo "python3 resolves to: $(which python3)"
python3 -m pytest --version 2>&1 | head -1
# fresh remote-agent (mimic Harbor upload)
rm -rf /tmp/remote-agent && mkdir -p /tmp/remote-agent
cp "$REPO/agent/run.sh" "$REPO/agent/local_agent.py" /tmp/remote-agent/
chmod +x /tmp/remote-agent/run.sh
if grep -q $'\r' /tmp/remote-agent/run.sh; then echo "WARN run.sh CRLF"; else echo "run.sh LF OK"; fi
python3 -m py_compile /tmp/remote-agent/local_agent.py && echo "agent compiles OK"
run_agent() {
  local task=$1 instr=$2 tmo=$3
  cd /tmp/remote-agent
  local start=$(date +%s)
  timeout "$tmo" sh ./run.sh "$instr" >"$PLOG/$task.agent.log" 2>&1
  local rc=$?
  local end=$(date +%s)
  cp "$PLOG/$task.agent.log" "$PLOG/$task.agent.log.bak" 2>/dev/null || true
  echo "$rc $((end-start))"
}
echo "=== BENCH2 START ==="
echo "--- hello-file ---"
rm -rf /app /tests /logs/verifier && mkdir -p /app /logs/verifier
INSTR=$(cat "$LT/hello-file/instruction.md")
read RC RT < <(run_agent hello-file "$INSTR" 100)
echo "agent rc=$RC runtime=${RT}s"
bash "$LT/hello-file/tests/test.sh"
echo "reward=$(cat /logs/verifier/reward.txt)"
echo "file: $(wc -c < /app/hello.txt 2>/dev/null || echo MISSING) [$(cat /app/hello.txt 2>/dev/null || echo MISSING)]"
echo "--- bye-file ---"
rm -rf /app /tests /logs/verifier && mkdir -p /app /logs/verifier
INSTR=$(cat "$LT/bye-file/instruction.md")
read RC RT < <(run_agent bye-file "$INSTR" 100)
echo "agent rc=$RC runtime=${RT}s"
bash "$LT/bye-file/tests/test.sh"
echo "reward=$(cat /logs/verifier/reward.txt)"
echo "file: $(wc -c < /app/bye.txt 2>/dev/null || echo MISSING) [$(cat /app/bye.txt 2>/dev/null || echo MISSING)]"
echo "--- incident-log-forensics ---"
rm -rf /app /tests /logs/verifier && mkdir -p /app/incident /logs/verifier
cp "$LT/incident-log-forensics/environment/collector_note.txt" "$LT/incident-log-forensics/environment/proxy_access.log" \
   "$LT/incident-log-forensics/environment/app.jsonl" "$LT/incident-log-forensics/environment/app_audit_recovered.jsonl" \
   "$LT/incident-log-forensics/environment/auth.log" "$LT/incident-log-forensics/environment/edge_decisions.log" \
   "$LT/incident-log-forensics/environment/edge_decisions_fragment.log" "$LT/incident-log-forensics/environment/dns_ptr_hints.txt" /app/incident/
chmod -R a+rX /app/incident
INSTR=$(cat "$LT/incident-log-forensics/instruction.md")
read RC RT < <(run_agent incident "$INSTR" 500)
echo "agent rc=$RC runtime=${RT}s"
bash "$LT/incident-log-forensics/tests/test.sh"
echo "reward=$(cat /logs/verifier/reward.txt)"
diff /app/incident_report.txt "$LT/incident-log-forensics/tests/expected_incident_report.txt" && echo "report byte-identical to expected"
echo "--- find-sqli-login ---"
rm -rf /app /tests /logs/verifier && mkdir -p /app /tests /logs/verifier
cp -r "$LT/find-sqli-login/environment/app/." /app/
cp "$LT/find-sqli-login/tests/test_security_report.py" /tests/
INSTR=$(cat "$LT/find-sqli-login/instruction.md")
read RC RT < <(run_agent findsqli "$INSTR" 500)
echo "agent rc=$RC runtime=${RT}s"
echo "--- agent log tail ---"; tail -15 "$PLOG/findsqli.agent.log"
ls -la /app/security_report.json 2>&1
bash "$LT/find-sqli-login/tests/test.sh"
echo "reward=$(cat /logs/verifier/reward.txt)"
tail -25 /logs/verifier/pytest_output.txt 2>/dev/null
echo "--- fix-sqli-login ---"
rm -rf /app && mkdir -p /app
cp -r "$LT/fix-sqli-login/environment/app/." /app/
INSTR=$(cat "$LT/fix-sqli-login/instruction.md")
read RC RT < <(run_agent fixlogin "$INSTR" 500)
echo "agent rc=$RC runtime=${RT}s"
echo "--- agent log tail ---"; tail -20 "$PLOG/fixlogin.agent.log"
sed -n '13,28p' /app/routers/auth.py
python3 -m py_compile /app/routers/auth.py && echo "compiles OK"
grep -c '\$1' /app/routers/auth.py || echo "no \$1"
if grep -q 'f"SELECT' /app/routers/auth.py; then echo "STILL VULNERABLE"; else echo "f-string SELECT gone (good)"; fi
echo "--- fix-sqli-search ---"
rm -rf /app && mkdir -p /app
cp -r "$LT/fix-sqli-search/environment/app/." /app/
INSTR=$(cat "$LT/fix-sqli-search/instruction.md")
read RC RT < <(run_agent fixsearch "$INSTR" 500)
echo "agent rc=$RC runtime=${RT}s"
echo "--- agent log tail ---"; tail -20 "$PLOG/fixsearch.agent.log"
sed -n '8,16p' /app/routers/items.py
python3 -m py_compile /app/routers/items.py && echo "compiles OK"
if grep -q "LIKE '%{q}%'" /app/routers/items.py; then echo "STILL VULNERABLE"; else echo "LIKE-injection gone (good)"; fi
echo "=== BENCH2 END ==="
