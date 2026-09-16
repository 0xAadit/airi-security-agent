#!/usr/bin/env bash
set -uo pipefail

LOG_DIR="/logs/verifier"
VERIFIER_LOG="$LOG_DIR/verifier.log"
APP_LOG="$LOG_DIR/app.log"
PYTEST_LOG="$LOG_DIR/pytest_output.txt"
DB_URL="postgresql://appuser:apppass@localhost:5432/appdb"
APP_PID=""

mkdir -p "$LOG_DIR"
: > "$VERIFIER_LOG"
: > "$APP_LOG"

log() {
    printf '[%s] %s\n' "$(date -Iseconds)" "$*" | tee -a "$VERIFIER_LOG"
}

write_reward() {
    printf '%s\n' "$1" > "$LOG_DIR/reward.txt"
}

cleanup() {
    if [[ -n "${APP_PID:-}" ]] && kill -0 "$APP_PID" 2>/dev/null; then
        kill "$APP_PID" 2>/dev/null || true
        wait "$APP_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT

log "Stopping any uvicorn process left by the agent"
pkill -f "uvicorn main:app" >> "$VERIFIER_LOG" 2>&1 || true
sleep 1

log "Starting PostgreSQL service"
service postgresql start >> "$VERIFIER_LOG" 2>&1 || service postgresql restart >> "$VERIFIER_LOG" 2>&1 || true
sleep 1

log "Recreating verifier database"
su postgres -c "psql -c \"CREATE USER appuser WITH PASSWORD 'apppass';\"" >> "$VERIFIER_LOG" 2>&1 || true
su postgres -c "psql -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'appdb';\"" >> "$VERIFIER_LOG" 2>&1 || true
su postgres -c "dropdb --if-exists appdb" >> "$VERIFIER_LOG" 2>&1 || true
su postgres -c "createdb appdb -O appuser" >> "$VERIFIER_LOG" 2>&1 || true

cd /app || {
    log "ERROR: /app directory not found"
    write_reward 0
    exit 0
}

if [[ -x "/app/.venv/bin/python" ]]; then
    PYTHON="/app/.venv/bin/python"
else
    PYTHON="python3"
fi

if [[ -x "/app/.venv/bin/uvicorn" ]]; then
    UVICORN="/app/.venv/bin/uvicorn"
else
    UVICORN="uvicorn"
fi

log "Starting application under verifier control"
DATABASE_URL="$DB_URL" "$UVICORN" main:app --host 127.0.0.1 --port 8000 --log-level info > "$APP_LOG" 2>&1 &
APP_PID=$!

log "Waiting for /healthz"
healthy=0
for _ in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/healthz >> "$VERIFIER_LOG" 2>&1; then
        healthy=1
        break
    fi
    if ! kill -0 "$APP_PID" 2>/dev/null; then
        log "ERROR: application process exited before becoming healthy"
        write_reward 0
        exit 0
    fi
    sleep 1
done

if [[ "$healthy" != "1" ]]; then
    log "ERROR: application did not become healthy within 30 seconds"
    write_reward 0
    exit 0
fi

log "Running hidden pytest verifier suite"
DATABASE_URL="$DB_URL" "$PYTHON" -m pytest /tests -v --tb=short > "$PYTEST_LOG" 2>&1
pytest_status=$?

if [[ "$pytest_status" == "0" ]]; then
    log "Hidden pytest verifier suite passed"
    write_reward 1
else
    log "Hidden pytest verifier suite failed with exit code $pytest_status"
    write_reward 0
fi

exit 0
