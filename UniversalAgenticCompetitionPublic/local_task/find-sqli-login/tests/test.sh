#!/usr/bin/env bash
set -uo pipefail

LOG_DIR="/logs/verifier"
VERIFIER_LOG="$LOG_DIR/verifier.log"
PYTEST_LOG="$LOG_DIR/pytest_output.txt"

mkdir -p "$LOG_DIR"
: > "$VERIFIER_LOG"
: > "$PYTEST_LOG"

log() {
    printf '[%s] %s\n' "$(date -Iseconds)" "$*" | tee -a "$VERIFIER_LOG"
}

write_reward() {
    printf '%s\n' "$1" > "$LOG_DIR/reward.txt"
}

if [[ -x "/app/.venv/bin/python" ]]; then
    PYTHON="/app/.venv/bin/python"
else
    PYTHON="python3"
fi

log "Running security report verifier"
"$PYTHON" -m pytest /tests -v --tb=short > "$PYTEST_LOG" 2>&1
pytest_status=$?

if [[ "$pytest_status" == "0" ]]; then
    log "Security report verifier passed"
    write_reward 1
else
    log "Security report verifier failed with exit code $pytest_status"
    write_reward 0
fi

exit 0
