#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
WORKDIR="${LOCAL_AGENT_WORKDIR:-$(pwd)}"

if [ "$#" -lt 1 ]; then
  echo "Usage: ./run.sh PROMPT"
  exit 1
fi

PROMPT="$*"

exec env LOCAL_AGENT_WORKDIR="$WORKDIR" python3 "$SCRIPT_DIR/local_agent.py" "$PROMPT"
