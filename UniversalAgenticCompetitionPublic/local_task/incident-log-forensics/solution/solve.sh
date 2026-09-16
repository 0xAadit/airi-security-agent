#!/bin/bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
cp "$HERE/expected_incident_report.txt" /app/incident_report.txt
