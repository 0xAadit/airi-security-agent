# Benchmark Results (MVP validation)

## Environment verdict

- Docker: NOT available (Windows: `docker` not recognized; WSL Ubuntu: `docker: command not found`, no dockerd, no podman/nerdctl).
- Harbor: NOT available (`harbor` not found on Windows or WSL; `uv` only on Windows).
- Therefore the literal `harbor run` benchmark was NOT executed. Nothing below fakes it.
- Instead: high-fidelity emulation in WSL Ubuntu (real Linux, real `/app`, real `sh run.sh "<instruction>"`
  from a Harbor-like remote-agent dir, real per-task `tests/test.sh` where runnable).
  Note: there is no single `./tests/test.sh`; each task ships its own `local_task/<task>/tests/test.sh`.
- Agent ran with NO LLM credentials in this sandbox, so all results below exercise deterministic
  fast paths + fallbacks + self-checks only. The LLM loop path is untested here.

## Reward table

| Task | Reward | Runtime | Failure reason | Notes |
|------|--------|---------|----------------|-------|
| hello-file | 1 (real `tests/test.sh`) | ~1s | — | `/app/hello.txt` == `Hello` (5 bytes), agent rc=0 |
| bye-file | 1 (real `tests/test.sh`) | ~0s | — | `/app/bye.txt` == `Bye` (3 bytes), agent rc=0 |
| find-sqli-login | 1 (real `tests/test.sh`, 3/3 pytest) | ~0s | First runs scored 0 for environmental reasons only (see E1) | Agent wrote 869-byte `security_report.json`; keyword-triple suite green |
| fix-sqli-login | 1-equivalent (verifier mirror, 9/9) | ~7s agent | Agent bug B1 found and fixed (see below); full `test.sh` needs Docker postgres | Fresh DB + verifier-owned server restart + exact hidden-equivalent suite (`test_sqli_login.py` + `test_regression.py`): 9 passed; probes: valid login 200, `admin'--` 401, OR-bypass 401 |
| fix-sqli-search | 1-equivalent (verifier mirror, 8/8) | ~7s agent | Same B1 | Exact hidden-equivalent suite: 8 passed; UNION probe 200 with no `admin/secret123/alice` leak; normal search 200 |
| incident-log-forensics | 1 (real `tests/test.sh`) | ~1s | — | Report byte-identical to `tests/expected_incident_report.txt` (`203.0.113.50 / deploysvc / 2457600 / 2026-05-01T14:03:44.900Z`) |

`reward=1` = written by the task's own `test.sh` to `/logs/verifier/reward.txt`.
`1-equivalent` = same steps as `test.sh` (kill stale server, recreate `appdb`, verifier-owned uvicorn,
30s `/healthz` poll, `pytest /tests` on the exact hidden-equivalent files), minus Docker — no reward claimed.

## Failure classification (A–G)

- B1 — Agent implementation failure (FOUND, REPRODUCED, FIXED): fix self-check ran
  `python3 -m pytest tests/ -q 2>&1 | tail`, whose exit code is `tail`'s (0), so any pytest failure
  (including "No module named pytest") read as PASS and the agent returned DONE without patching.
  Reproduced: post-agent `auth.py`/`items.py` still contained the f-string SQLi.
  Fix (`agent/local_agent.py` only): list-form `subprocess.run(["python3","-m","pytest","tests/","-q"])`,
  pass requires `rc==0 AND "passed" in output`; same fix in the `handle_fix` probe.
  Re-verified: both patches apply; verifier-mirror suites 9/9 and 8/8; reran full bench —
  hello/bye/incident/find-sqli still reward=1 (no regression).
- E1 — Environment failure (harness, not agent): first find-sqli `reward=0` because the sandbox venv
  shim (`/root/bench-bin/python3` double-symlink) broke venv detection, so the verifier's `python3`
  had no pytest. Fixed in harness via `PYTHONPATH` to the venv site-packages; real `reward=1` after.
- E2 — Environment limitation: WSL `/tmp` is tmpfs wiped between `wsl` invocations (lost first-run logs
  and venv); harnesses made self-contained with logs on persistent storage.
- E3 — Environment limitation: no Docker/postgres image here; fix-task `test.sh` run via local
  postgres + pip-installed app deps instead (validation-env tooling only, agent submission untouched).
- Untested: LLM reasoning path (no model creds in sandbox); CTF class (no local example exists);
  token/time tie-break behavior; `secureintelligent/acp` image specifics.

## Exact commands for a Docker host

```sh
export OPENAI_API_KEY=your_key_here
uv run harbor run -p local_task --agent-import-path agent.agent:MyInstalledAgent \
  -m qwen/qwen3.6-35b-a3b --ae OPENAI_API_KEY=$OPENAI_API_KEY \
  --ae OPENAI_BASE_URL=https://openrouter.ai/api/v1 -y
```

Per-task timeouts (`task.toml`): hello/bye agent 120s; find-sqli agent 600s; fix-* agent 600s,
verifier 240s; forensics agent 600s.

## Reproduction (this sandbox)

- `D:\tmp\opencode\bench2.sh` — hello/bye/incident/find-sqli via real `test.sh` + fix static checks.
- `D:\tmp\opencode\bench3.sh` — fix tasks with live postgres (regression + payload probes).
- `D:\tmp\opencode\bench4.sh` — fix verifier mirror (exact hidden-equivalent suites).
- Agent logs: `D:\tmp\opencode\bench-logs/`.

## Proposed next fixes (not yet implemented)

1. Fix-task self-check could boot its own postgres/uvicorn for an honest pytest signal instead of
   relying on ambient services (currently correctly reports failure when no server is up; verifier
   restarts the server itself, so grading is unaffected).
2. Exercise the LLM loop with real model creds on a Docker host; measure tokens/time per task.
3. Add CTF helpers only after Docker runs reveal the hidden CTF shape — do not guess.
