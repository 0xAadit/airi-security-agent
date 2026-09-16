# Migration Checkpoint (Windows -> Arch Linux)

- Repository URL: https://github.com/0xAadit/airi-security-agent
- Branch: `main`
- Commit SHA: `260dd32b2a3b55252be7825767a6371a78c37f80`
- Checkpoint commit message: `checkpoint: AIRI MVP before Linux migration`
- Upstream competition repo (NOT included as git history):
  https://github.com/SecureIntelligent/UniversalAgenticCompetitionPublic
  at `b95c62fec81656e338af54045efa688fd4979615`
  (its `.git` was removed so our modified agent + fixtures track as normal files;
  only local change vs upstream is `UniversalAgenticCompetitionPublic/agent/local_agent.py`).

## Current project status

MVP single-agent implementation complete and locally validated without Docker/LLM.
No Docker, Harbor, or LLM credentials existed in the Windows/WSL sandbox.

## What has been implemented

- `UniversalAgenticCompetitionPublic/agent/local_agent.py` (~52KB, stdlib only):
  deterministic task router (trivial/audit/fix/forensics/generic), 7 tools
  (bash/read/list/search/write-overwrite/patch/append), text-based LLM ReAct loop
  (urllib POST to `OPENAI_BASE_URL`, `FINAL:` protocol, sliding history, usage accounting),
  verifier-mirror self-checks, deterministic fallbacks, `--smoke-test` mode.
- `run.sh` unchanged (Harbor contract intact).
- `docs/REVERSE_ENGINEERING.md`, `docs/BENCHMARK_RESULTS.md`, `docs/LLM_RUNTIME_CHECKLIST.md`.
- `validation/` WSL harnesses (`bench2/3/4.sh`, `inspect.sh`) — update `REPO=` path on Arch.

## What has been tested (WSL Ubuntu, real /app, real run.sh/test.sh, no LLM)

- hello-file: reward=1. bye-file: reward=1. incident-log-forensics: reward=1 (byte-exact).
- find-sqli-login: reward=1 (3/3 pytest via real `test.sh`).
- fix-sqli-login: verifier mirror 9/9 (fresh DB + restarted server + hidden-equivalent suite).
- fix-sqli-search: verifier mirror 8/8. Probes: bypasses 401, UNION no-leak.
- Real bug found+fixed: pytest pipe exit-code masking (`tail` hid failures).
- `--smoke-test` without creds honestly reports `skip`.

## What has NOT been tested

- Literal `harbor run` (no Docker/Harbor here). LLM loop against a live endpoint.
- CTF task class (no local example). `secureintelligent/acp` image specifics. Token/time tie-break.

## Exact next steps on Arch

1. `git clone https://github.com/0xAadit/airi-security-agent && cd airi-security-agent`.
2. Install: `docker`, `uv`, `harbor` (via uv/pipx), `python3`, `pytest`, `postgresql + fastapi uvicorn asyncpg httpx` (validation only).
3. Pull `secureintelligent/acp:latest`.
4. Set `OPENAI_API_KEY` (+ `OPENAI_BASE_URL` for local endpoint); run:
   `uv run harbor run -p UniversalAgenticCompetitionPublic/local_task --agent-import-path agent.agent:MyInstalledAgent -m <model> --ae OPENAI_API_KEY=$OPENAI_API_KEY --ae OPENAI_BASE_URL=<url> -y`
   from inside `UniversalAgenticCompetitionPublic/`.
5. Run `python3 UniversalAgenticCompetitionPublic/agent/local_agent.py --smoke-test` first for LLM proof.
6. Order: hello, bye, find-sqli, fix-login, fix-search, forensics; update `docs/BENCHMARK_RESULTS.md`.

## Environment variables required

`LOCAL_AGENT_MODEL` (via harbor `-m`), `OPENAI_BASE_URL` + `OPENAI_API_KEY` (via `--ae`).
Never commit values; export in shell only.

## Dependencies / setup

Agent runtime: none beyond `secureintelligent/acp` image (stdlib only, ~52KB submission).
Validation host: docker, uv, harbor, python3, pytest, postgresql, fastapi, uvicorn, asyncpg, httpx.

## Important known issues

- WSL `/tmp` is tmpfs wiped between sessions — keep harnesses self-contained, logs persistent.
- Venv-through-symlink breaks venv detection; prefer `PYTHONPATH` for pytest shims.
- Fix-task self-check needs a running server for a green pytest signal; verifier restarts it anyway.
- `validation/*.sh` hardcode `/mnt/d/...` paths — edit `REPO=` on Arch.

## Must NOT change during migration

- `agent/run.sh` semantics and Harbor contract (`agent/agent.py` stays upstream-identical).
- Deterministic handlers unless a Docker-backed failure proves a bug (no speculative rewrites).
- 10MB submission limit, offline-only runtime, no new agent dependencies.
