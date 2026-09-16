#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_APP="$SCRIPT_DIR/app"
VARIANTS_DIR="$SCRIPT_DIR/variants"
TASKS_DIR="$(dirname "$SCRIPT_DIR")"

KNOWN_TASKS=(fix-sqli-login fix-sqli-search)
dry_run=0
target_tasks=()

usage() {
    echo "Usage: $0 [--all | --task <task-name>] [--dry-run]"
    echo "Known tasks: ${KNOWN_TASKS[*]}"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)   target_tasks=("${KNOWN_TASKS[@]}") ;;
        --task)  shift; target_tasks+=("$1") ;;
        --dry-run) dry_run=1 ;;
        *) usage ;;
    esac
    shift
done

[[ ${#target_tasks[@]} -eq 0 ]] && usage

for task in "${target_tasks[@]}"; do
    dest="$TASKS_DIR/$task/environment/app"

    if [[ ! -d "$TASKS_DIR/$task" ]]; then
        echo "ERROR: task directory not found: $TASKS_DIR/$task" >&2
        exit 1
    fi
    if [[ ! -d "$VARIANTS_DIR/$task" ]]; then
        echo "ERROR: variant not found: $VARIANTS_DIR/$task" >&2
        exit 1
    fi

    echo "Syncing $task → $dest"
    if [[ $dry_run -eq 0 ]]; then
        rm -rf "$dest"
        cp -r "$SOURCE_APP" "$dest"
        cp -r "$VARIANTS_DIR/$task/." "$dest/"
        echo "  OK"
    else
        echo "  [dry-run] cp -r $SOURCE_APP $dest"
        echo "  [dry-run] cp -r $VARIANTS_DIR/$task/. $dest/"
    fi
done

echo "Done."
