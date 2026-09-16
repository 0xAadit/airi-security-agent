#!/bin/bash
set -euo pipefail

REPORT=/app/incident_report.txt
TESTS_DIR=$(cd "$(dirname "$0")" && pwd)
EXPECTED="$TESTS_DIR/expected_incident_report.txt"
REWARD=/logs/verifier/reward.txt

mkdir -p "$(dirname "$REWARD")"

fail() {
  echo 0 >"$REWARD"
  exit 0
}

[[ -f "$REPORT" ]] || fail
[[ -f "$EXPECTED" ]] || fail

# Exactly four non-empty lines, all key=value
LINE_COUNT=$(grep -cve '^$' "$REPORT" || true)
[[ "$LINE_COUNT" -eq 4 ]] || fail

while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" ]] && fail
  [[ "$line" =~ ^[a-z_]+=.+$ ]] || fail
  key="${line%%=*}"
  val="${line#*=}"
  [[ -n "$key" && -n "$val" ]] || fail
  [[ "$line" == *" = "* ]] && fail
done <"$REPORT"

TMP_GOT=$(mktemp)
TMP_EXP=$(mktemp)
trap 'rm -f "$TMP_GOT" "$TMP_EXP"' EXIT

normalize_and_sort() {
  sed 's/\r$//' "$1" | LC_ALL=C sort
}

normalize_and_sort "$REPORT" >"$TMP_GOT"
normalize_and_sort "$EXPECTED" >"$TMP_EXP"
if diff -q "$TMP_GOT" "$TMP_EXP" >/dev/null; then
  echo 1 >"$REWARD"
else
  echo 0 >"$REWARD"
fi
