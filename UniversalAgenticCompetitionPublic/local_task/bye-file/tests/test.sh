#!/bin/bash
set -e

if [ -f /app/bye.txt ] && [ "$(cat /app/bye.txt)" = "Bye" ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
