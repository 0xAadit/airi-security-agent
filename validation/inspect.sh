#!/bin/bash
ls -la /tmp/bench-logs/
for f in /tmp/bench-logs/*.log; do
  echo "== $f"
  wc -c "$f"
  head -c 2000 "$f"
  echo
  echo "----"
done
echo "=== shim ==="
ls -la /tmp/bench-bin/
echo "=== python3 resolution ==="
export PATH="/tmp/bench-bin:/usr/local/bin:/usr/bin:/bin"
which python3
python3 -m pytest --version 2>&1 | head -2
