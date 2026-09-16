#!/bin/bash
set -e

if [ -f /app/hello.txt ] && [ "$(cat /app/hello.txt)" = "Hello" ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
