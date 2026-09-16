#!/usr/bin/env bash
set -e

service postgresql start
sleep 2

su postgres -c "psql -c \"CREATE USER appuser WITH PASSWORD 'apppass';\" 2>/dev/null || true"
su postgres -c "psql -c \"CREATE DATABASE appdb OWNER appuser;\" 2>/dev/null || true"

uvicorn main:app --host 0.0.0.0 --port 8000 &

# Keep the container alive even if the app process is killed by an agent. The
# verifier owns restarting uvicorn from the submitted code before grading.
tail -f /dev/null
