# AIRI Competition Reverse Engineering

> Note on location: repo has no existing `docs/` convention (root contains only `UniversalAgenticCompetitionPublic/`, `work/`, `instructions.md` — verified by directory listing), so `docs/` was created as the sensible location per the `research` skill rule.
> All claims below are derived from primary sources in `instructions.md` and `UniversalAgenticCompetitionPublic/`. Citations are `path:line[-line]`.

## 1. Official Requirements

- Goal: universal autonomous infosec agent for isolated environments where public LLMs/internet are prohibited; must work with small local LLMs (`instructions.md:10-12`).
- Deliverable: `.zip` archive ≤10 MB containing at minimum `run.sh` plus necessary source files (`instructions.md:33-35`; `README.md:87-91`).
- Runtime: agent is deployed in provided runtime image, receives **task instruction text as input** (`instructions.md:16`), must run correctly in `secureintelligent/acp` Docker container (`instructions.md:16`).
- Isolation: during execution only local environment resources + local LLM endpoint are accessible via `LOCAL_AGENT_MODEL`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`; **installing additional dependencies at runtime is not possible** (`instructions.md:16`; `README.md:103-113`).
- Solution must be reproducible, resilient to environmental limitations (`instructions.md:16`).
- Evaluation: **15 independent tasks, binary scoring** 1=solved / 0=not solved (`instructions.md:20`). Pool covers code vuln detection, forensics, SWE-bench-like security fixes, CTF classes (`instructions.md:20`; `README.md:26-31`). Each problem has its own time and token limits (`instructions.md:20`; `README.md:43`).
- Final score = (sum of task scores) / (total tasks) (`instructions.md:41-44`).
- Tie-break: (1) fewer total LLM input+output tokens across all tasks ranks higher; (2) if equal, shorter total wall time from agent startup to completion (`instructions.md:61-64`; `README.md:45`).
- Team size 2–4 stated in header (`instructions.md:2`). Main-stage result explicitly not counted toward final/online-defense winner (`instructions.md:46`).
- Checkpoints CP1–CP7 with upload/result dates Jul 27–Sep 22 Moscow time; checkpoint principle, no instant leaderboard, one latest solution per team per checkpoint (`instructions.md:72-127`).
- Must run without internet in `secureintelligent/acp`, otherwise scored 0 (`instructions.md:68`).
- Local dev repo: `https://github.com/SecureIntelligent/UniversalAgenticCompetitionPublic` (`instructions.md:31`, `instructions.md:131-133`); local tasks are dev-only, not the closed benchmark (`README.md:3-7`).

## 2. Runtime Contract

- Harbor wrapper `class MyInstalledAgent(BaseInstalledAgent)` in `agent/agent.py:10` is the **required interface, identical for all participants** (`README.md:55`, `README.md:98`).
- Constants: `REMOTE_DIR = "/opt/harbor/local-agent"` (`agent/agent.py:11`), `OUTPUT_FILENAME = "local-agent.txt"` (`agent/agent.py:12`), `SETUP_LOG_FILENAME = "setup.log"` (`agent/agent.py:13`).
- `install()`: creates `REMOTE_DIR` as root, uploads entire local `agent/` dir to `REMOTE_DIR`, `chmod +x REMOTE_DIR/run.sh` (`agent/agent.py:32-41`). Setup commands are wrapped with timestamped logging to `$AGENT_DIR/setup.log` (`agent/agent.py:19-30`).
- `run()`: executed with `cwd=self.REMOTE_DIR` (`agent/agent.py:67`):
  ```sh
  ./run.sh "<task instruction>" 2>&1 | tee <agent_dir>/local-agent.txt
  ```
  (`agent/agent.py:60-68`; `README.md:160-163`).
- `run.sh` contract (`agent/run.sh:1-14`):
  - `#!/bin/sh` + `set -eu` (`agent/run.sh:1-2`).
  - `SCRIPT_DIR` resolved from `$0`; `WORKDIR="${LOCAL_AGENT_WORKDIR:-$(pwd)}"` (`agent/run.sh:4-5`).
  - Requires ≥1 arg else `Usage: ./run.sh PROMPT`, exit 1 (`agent/run.sh:7-10`).
  - `PROMPT="$*"` — **all argv elements joined with spaces** (`agent/run.sh:12`).
  - `exec env LOCAL_AGENT_WORKDIR="$WORKDIR" python3 "$SCRIPT_DIR/local_agent.py" "$PROMPT"` (`agent/run.sh:14`).
- Submission layout: `sample_submission.zip` contains exactly `sample_submission/`, `sample_submission/run.sh`, `sample_submission/local_agent.py` (verified via `unzip -l` equivalent). `agent/agent.py` must NOT be included — it is auto-added/overwritten at evaluation (`README.md:94-98`).
- Agent stdout+stderr is teed to `local-agent.txt` but **not graded**; grading is via filesystem/service side effects (see §4). `context.metadata` records `remote_dir`/`output_file` (`agent/agent.py:70-73`).

## 3. Input

- Single string: task instruction text, passed as one shell-quoted arg to `run.sh`, then re-joined via `$*` (`agent/agent.py:63`; `agent/run.sh:12`).
- `local_agent.py` joins argv again with `" ".join(args.prompt)` (`agent/local_agent.py:315-318`), so newlines/quoting in the original instruction are **flattened to spaces** — agent must not depend on exact whitespace.
- Workdir: `LOCAL_AGENT_WORKDIR` if set else `Path.cwd()` (`agent/local_agent.py:93-97`). At eval, Harbor sets cwd to `REMOTE_DIR` (`agent/agent.py:67`), so initial workdir is `/opt/harbor/local-agent`, **not** `/app`. All local task instructions instead say work happens in `/app` (e.g. `local_task/fix-sqli-login/instruction.md:1`, `local_task/find-sqli-login/instruction.md:1`, `local_task/incident-log-forensics/instruction.md:5`).
- Instruction shapes observed:
  - Trivial: one sentence, exact path + exact content (`local_task/hello-file/instruction.md:1`, `local_task/bye-file/instruction.md:1`).
  - Audit: "working in `/app`, FastAPI+Postgres, do not modify code, write JSON report to fixed path + schema" (`local_task/find-sqli-login/instruction.md:1-27`).
  - Fix: "working in `/app`, run `pytest tests/`, all tests must still pass, analyse+fix most critical issues, no new deps beyond `pyproject.toml`" (`local_task/fix-sqli-login/instruction.md:1-7`, identical in `fix-sqli-search`).
  - Forensics: ticket narrative + artifact dir `/app/incident/` + strict 4-line `key=value` deliverable + normative field mapping (`local_task/incident-log-forensics/instruction.md:1-32`).
- In-task hints: FastAPI tasks ship `app/AGENTS.md:1-36` (run `pytest tests/`, stale-`uvicorn` handling, minimal diffs, DB persists). Forensics ships `collector_note.txt`, `dns_ptr_hints.txt` with explicit distractor warnings (see §9).

## 4. Output

- Evaluator expects **persistent side effects**, not stdout. Stdout only goes to `local-agent.txt` (`agent/agent.py:62-63`).
- Success signal is `/logs/verifier/reward.txt` containing `1` or `0`, written by each task's `tests/test.sh`:
  - `hello-file/tests/test.sh:4-7`: `1` iff `/app/hello.txt` exists and `cat` equals `Hello`.
  - `bye-file/tests/test.sh:4-7`: same for `/app/bye.txt` == `Bye`. Note `[ "$(cat ...)" = ... ]` strips trailing newlines, so trailing newline is tolerated despite "no trailing newline required" (`hello-file/instruction.md:1`).
  - `find-sqli-login/tests/test.sh:27-38`: runs `pytest /tests`, `1` iff exit 0. Test logic in `tests/test_security_report.py:21-82` (existence, valid JSON, `findings` non-empty array, keyword-triple match — see §9).
  - `fix-sqli-*/tests/test.sh:89-99`: runs hidden `pytest /tests`, `1` iff exit 0. Verifier **restarts the app itself**: kills agent `uvicorn` (`test.sh:32-34`), restarts postgres + recreates `appdb` (`test.sh:36-44`), starts `DATABASE_URL=... uvicorn main:app --host 127.0.0.1 --port 8000` (`test.sh:64-66`), polls `/healthz` ≤30s (`test.sh:68-87`), then pytest (`test.sh:90`).
  - `incident-log-forensics/tests/test.sh:16-45`: `0` unless `/app/incident_report.txt` exists, has exactly 4 non-empty lines, each matches `^[a-z_]+=^.+$` with no ` = `, and sorted CRLF-normalized content diffs equal to `tests/expected_incident_report.txt`.
- All observed `test.sh` verifiers end with `exit 0` (`fix-sqli-login/tests/test.sh:101`, `find-sqli-login/tests/test.sh:38`, `incident-log-forensics/tests/test.sh:46` is via `fail()`/`echo` paths) — **exit code does not carry the score; `reward.txt` does**.
- Minimum valid submission: zip with executable-equivalent `run.sh` at top level (Harbor `chmod +x`s it anyway, `agent/agent.py:39-41`). Anything else (e.g. `local_agent.py`) rides alongside and is invoked from `run.sh` (`README.md:100`).

## 5. LLM Interface

- Only LLM access in eval is the local endpoint described by three env vars (`README.md:107-111`; `instructions.md:16`): `LOCAL_AGENT_MODEL`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`.
- Template resolves model as `LOCAL_AGENT_MODEL` else `OPENAI_MODEL`, else raises (`agent/local_agent.py:113-119`); `OPENAI_BASE_URL`/`OPENAI_API_KEY` are required (`agent/local_agent.py:106-110`, `agent/local_agent.py:230-231`).
- Harbor passes through only what is set: `LOCAL_AGENT_MODEL` from `-m`, plus `OPENAI_BASE_URL`/`OPENAI_API_KEY` from `--ae` (`agent/agent.py:48-58`).
- Client is OpenAI-compatible: `OpenAIChatModel(model_name, provider=OpenAIProvider(base_url, api_key))` via `pydantic-ai` (`agent/local_agent.py:232-239`).
- Local dev command uses OpenRouter as a stand-in (`README.md:63-73`):
  ```sh
  export OPENAI_API_KEY=your_key_here
  uv run harbor run -p local_task --agent-import-path agent.agent:MyInstalledAgent -m qwen/qwen3.6-35b-a3b --ae OPENAI_API_KEY=$OPENAI_API_KEY --ae OPENAI_BASE_URL=https://openrouter.ai/api/v1 -y
  ```
- Template loop cap: `REQUEST_LIMIT = 1000` via `UsageLimits(request_limit=...)` (`agent/local_agent.py:20`, `agent/local_agent.py:302-307`). No token cap in template; per-task token/time limits are enforced by the closed harness (`README.md:43`; `instructions.md:20`).
- Eval model is an undisclosed **small local LLM**; local `-m` choice does not transfer to eval. Prompt must therefore be short, explicit, low-reasoning-depth.

## 6. Available Tools

Template `local_agent.py` exposes exactly four LLM tools (`agent/local_agent.py:249-267`) with system prompt "non-interactive coding agent ... inspect files, run commands, apply focused diffs ... concise steps" (`agent/local_agent.py:241-246`):

- `bash(command: str)` → `_run_bash` (`agent/local_agent.py:153-178`): `asyncio.create_subprocess_shell` with `cwd=workdir`, captures stdout+stderr, returns `$ cmd / [cwd] / [exit_code] / [stdout] / [stderr]`, truncated to `MAX_TOOL_OUTPUT_CHARS = 16000` (`agent/local_agent.py:18`, `agent/local_agent.py:30-33`). Only generic shell — `grep`/`rg`, `find`, `curl`, `ps`, `pkill`, `pytest`, `python3`, `uvicorn`, `patch` are reached through it.
- `read_file(path: str)` → `_read_file` (`agent/local_agent.py:181-194`): resolves absolute as-is else `workdir/path` (`agent/local_agent.py:100-103`), returns `File not found`/`Not a file` strings on error, UTF-8 + 16k truncation.
- `apply_diff(path: str, diff_content: str)` → `_apply_unified_diff` via `patch -N -r - <file>` (`agent/local_agent.py:122-150`), fails cleanly if file missing/not-a-file (`agent/local_agent.py:197-210`). Requires valid unified diff; no full-file overwrite primitive.
- `append_file(path: str, content: str)` → creates parents + appends (`agent/local_agent.py:213-225`). Only way to create new files without shell.
- Observability: JSONL-ish `[local-agent] {...}` stdout logs; secret keys containing `api_key/apikey/token/secret/password` redacted; values truncated to 16k (`agent/local_agent.py:22`, `agent/local_agent.py:46-62`). Stream events logged: `llm_tool_call`, `llm_tool_result`, `agent_done` (`agent/local_agent.py:65-90`, `agent/local_agent.py:272-288`).
- What the template lacks: no dedicated write/overwrite, glob, grep, or HTTP tool; everything beyond the four tools must go through `bash`.

## 7. Runtime Environment

- Base image `secureintelligent/acp:latest`, Python 3.12 (`README.md:115-117`). All task Dockerfiles start `FROM secureintelligent/acp:latest` (e.g. `local_task/hello-file/environment/Dockerfile:1`, `local_task/fix-sqli-login/environment/Dockerfile:1`).
- Pinned Python deps include `harbor==0.16.1`, `openai`, `anthropic`, `google-genai`, `litellm`, `langchain*`, `langgraph`, `llama-index`, `openai-agents`, `pydantic-ai>=1.44.0`, `tenacity`, `tiktoken`, etc. (`README.md:119-148`).
- APT tools preinstalled: `build-essential`, `cmake`, `curl`, `git`, `jq`, `openssl`, `ripgrep`, `tcpdump`, `traceroute`, `tree`, `unzip`, `wget`, `zip`, plus standard debugging/network utilities (`README.md:152-154`).
- Task images add: `apt-get install -y postgresql` for FastAPI tasks (`fix-sqli-login/environment/Dockerfile:3-5`, identical in `fix-sqli-search`, `find-sqli-login`); `WORKDIR /app; COPY app/ .; /app/.venv/bin/uv pip install ... .` (`fix-sqli-login/environment/Dockerfile:7-9`); `EXPOSE 8000; ENTRYPOINT ["/entrypoint.sh"]` (`.../Dockerfile:13-15`).
- Entrypoints: `service postgresql start; sleep 2; CREATE USER appuser / DATABASE appdb; uvicorn main:app --host 0.0.0.0 --port 8000 &; tail -f /dev/null` (`find-sqli-login/environment/entrypoint.sh:1-14`, identical in both `fix-sqli-*`). `tail -f /dev/null` keeps container alive if agent kills uvicorn; verifier restarts uvicorn itself before grading.
- App deps per task (`find-sqli-login/environment/app/pyproject.toml:1-11`, same in `fix-sqli-*` and `insecure-api-app/app/pyproject.toml:1-11`): `fastapi`, `uvicorn[standard]`, `asyncpg`, `httpx`, `pytest`. Python venv at `/app/.venv`; verifiers prefer `/app/.venv/bin/python|uvicorn` with fallback to system (`fix-sqli-login/tests/test.sh:52-62`).
- Line endings enforced: `*.sh text eol=lf`, `*.txt text eol=lf` (`.gitattributes:1-2`); 2026-08-26 update made incident verification CRLF-tolerant (`README.md:11`).

## 8. Local Benchmark

- Command and flag meanings (`README.md:71-83`): `-p local_task` (task path), `--agent-import-path agent.agent:MyInstalledAgent` (wrapper), `-m <model>` (→ `LOCAL_AGENT_MODEL`), `--ae KEY=VAL` (forward env), `-y` (non-interactive).
- 7 entries under `local_task/`: `hello-file`, `bye-file`, `find-sqli-login`, `fix-sqli-login`, `fix-sqli-search`, `incident-log-forensics`, `insecure-api-app` (directory listing). Only the first six have `task.toml` + `tests/`; `insecure-api-app/` is a **dev source tree, not a runnable task** (no `task.toml`/`tests/test.sh`; has `sync.sh` + `app/` + `variants/`).
- Per-task budgets from `task.toml` (`schema_version = "1.2"` everywhere):
  | task | `[agent] timeout` | `[verifier] timeout` | cpus / mem |
  |---|---|---|---|
  | hello-file, bye-file | 120s (`hello-file/task.toml:18`, `bye-file/task.toml:18`) | 120s (`:15`) | 1 / 2048MB (`:22-23`) |
  | find-sqli-login | 600s (`find-sqli-login/task.toml:18`) | 120s (`:15`) | 2 / 4096MB (`:22-23`) |
  | fix-sqli-login, fix-sqli-search | 600s (`fix-sqli-login/task.toml:18`) | 240s (`:15`) | 2 / 4096MB (`:22-23`) |
  | incident-log-forensics | 600s (`incident-log-forensics/task.toml:18`) | 120s (`:15`) | 1 / 2048MB (`:22-23`) |
  All: `storage_mb=10240, gpus=0, allow_internet=true, mcp_servers=[]` (`task.toml:24-27` in each). `allow_internet=true` is local-only; eval is offline (`instructions.md:68`).
- Reference solutions in each `solution/solve.sh` (trivial `printf` for hello/bye; JSON heredoc for audit; `pathlib` string-replace patch + `pytest` for fixes; `cp expected_...` for forensics).
- `insecure-api-app/sync.sh:1-55` is the source of truth for fix tasks: `KNOWN_TASKS=(fix-sqli-login fix-sqli-search)` (`sync.sh:9`); sync = `rm -rf <task>/environment/app; cp -r app <dest>; cp -r variants/<task>/. <dest>/` (`sync.sh:44-48`). Fix #2026-07-09 notes reference solutions were re-synced to current sources (`README.md:13`).
- `local_task/` is explicitly not the final benchmark (`README.md:7`); use it to validate the run contract, tool loop, and verifier shapes.

## 9. Task Classes

Mapping to the four announced classes (`instructions.md:20`; `README.md:26-31`):

- **Smoke / file creation** (`hello-file`, `bye-file`; `category="programming"`, `difficulty="easy"` in `task.toml:10-12`): write exact bytes to `/app/hello.txt|bye.txt`. Capability: basic shell + absolute paths. No LLM reasoning needed.
- **Vuln detection / audit** (`find-sqli-login`; `category="security"`, tags `sqli,fastapi,postgresql,bug-bounty,audit,report` in `task.toml:12`): do NOT modify code; emit `/app/security_report.json` with `{findings:[{title,severity,category,location,evidence,impact,recommendation}]}` (`find-sqli-login/instruction.md:9-25`). Grader is keyword-based, not LLM-judged: needs one finding whose flattened lowercase text contains (a) an SQLi signal (`sql injection|sqli|...|parameterized|...`), AND (b) a login signal (`login|/login|auth|...|routers/auth.py|...`), AND (c) an exploit-detail signal (`bypass|admin'--|or '1'='1|password|req.username|fetchrow|...`) (`find-sqli-login/tests/test_security_report.py:37-82`). Reference finding names `POST /login` in `routers/auth.py` with `admin'--` / `OR '1'='1` bypass and `$1/$2` remediation (`find-sqli-login/solution/solve.sh:4-18`). Env quirk: only `auth.py` is vulnerable here; `items.py` is already `CLEAN: parameterized LIKE` (`find-sqli-login/environment/app/routers/items.py:12-16`).
- **Remediation / SWE-bench-like** (`fix-sqli-login`, `fix-sqli-search`; `difficulty="medium"`, tags `code-fix` in `task.toml:10-12`): patch the single planted SQLi, keep `pytest tests/` green. Vulns:
  - login: f-string `WHERE username = '{req.username}' AND password = '{req.password}'` + `fetchrow(query)` (`fix-sqli-login/environment/app/routers/auth.py:17-22`) → fix to `fetchrow("... $1 ... $2", req.username, req.password)` (`fix-sqli-login/solution/solve.sh:10-23`). Hidden checks: `admin'--` and `admin' OR '1'='1` must NOT return 200 (`fix-sqli-login/tests/test_sqli_login.py:1-17`) + full regression (valid login 200, wrong→401, search/items/comments/tags/users) (`fix-sqli-login/tests/test_regression.py:1-78`).
  - search: f-string `LIKE '%{q}%'` (`fix-sqli-search/environment/app/routers/items.py:12-14`) → fix to `fetch( "... LIKE $1", f"%{q}%")` (`fix-sqli-search/solution/solve.sh:10-20`). Hidden check: UNION payload `x' UNION SELECT ... FROM users--` must return 200 but leak none of `admin/secret123/alice/...` (`fix-sqli-search/tests/test_sqli_search.py:1-17`) + same regression suite.
  - Each task's other endpoint is already clean (`fix-sqli-login/.../items.py:12-16` CLEAN; `fix-sqli-search/.../auth.py:17-22` CLEAN) — confirms one-vuln-per-task design. Capabilities: grep for sinks, parameterized-query edit, restart/curl/pytest loop per `AGENTS.md`.
- **Forensics / log correlation** (`incident-log-forensics`; `difficulty="medium"`, tags `forensics,logs,correlation` in `task.toml:12`): reconcile `/app/incident/` (copied from `environment/` by `incident-log-forensics/environment/Dockerfile:7-10`) and write `/app/incident_report.txt` with exactly 4 `key=value` lines, no spaces/blank lines/commentary (`instruction.md:18-24`). Normative mapping: `compromised_user`=record `identity.subject`; `exfil_bytes`=`audit.payload_logical_bytes` else `audit.bytes`; `first_malicious_event_utc`=record `ts` verbatim; `attacker_ip`=proxy XFF for matched request (`instruction.md:27-31`). Ground truth (`tests/expected_incident_report.txt:1-4`): `203.0.113.50 / deploysvc / 2457600 / 2026-05-01T14:03:44.900Z`. Authoritative derivation in `scripts/check_parity.py:137-213`: merge `app.jsonl` + `app_audit_recovered.jsonl`, filter `14:03:00–14:04:59.999Z` + `audit.event==sensitive_export` + `request_id` in CONFIRM_SENSITIVE edge set (both `edge_decisions*.log`), pick max `payload_logical_bytes||bytes` with latest-ts tiebreak, then map XFF to last public IP. Designed distractors: truncated primary (25k noise lines in `app.jsonl` vs 3-line WORM fragment in `app_audit_recovered.jsonl:1-3` holding the winner); load-balancer `10.0.0.5` vs XFF chain; multi-line proxy record with tab continuation (`proxy_access.log:12-13`); 304-duplicate and size-mismatched decoys; `edge_decisions.log` (EDT `-04:00`) vs fragment with stray space `request_id= telemetry-lolt-441` (`edge_decisions_fragment.log:2`); `auth.log` in `America/New_York` civil time (`auth.log:1`) vs UTC artifacts; stale `dns_ptr_hints.txt:1-7` explicitly non-authoritative. Capabilities: JSONL/`grep`/`python3` correlation, timezone care, verbatim copy, strict formatting.
- **CTF-style**: announced (`instructions.md:20`; `README.md:31`) but **no local example** — shape unknown (see §14). Expect flag-file / service-exploit / crypto-misc variants in closed set.

## 10. Constraints

- Time: per-task `[agent] timeout_sec` (120s trivial, 600s others — §8) plus undisclosed per-task limits in closed eval (`instructions.md:20`). Tie-break rewards faster total time (`instructions.md:64`).
- Tokens: per-task token limits in closed eval (`instructions.md:20`; `README.md:43`); tie-break rewards fewer total tokens (`instructions.md:63`). Template has no token cap besides 1000 requests (`agent/local_agent.py:20`).
- Compute: 1–2 CPUs, 2048–4096 MB RAM, ~10 GB storage, 0 GPUs locally (`task.toml:22-25`); assume similar or tighter in eval. Verifier `build_timeout_sec=600` (`task.toml:21`).
- Team/effort: ~40 h, 2-person team per task brief — optimize for implementation speed and reliability over novelty.
- Filesystem: tasks assume `/app` is writable; incident expects `/app/incident/` readable and `/app/incident_report.txt` writable; DB-backed tasks expect `/app/routers/*.py` editable. Writability outside `/app` and of `/logs`, `/tests` in eval is unconfirmed (local `test.sh` paths use `/logs/verifier`, `/tests`).
- Processes: agent may `pkill`/`restart` uvicorn for local validation, but verifier owns the final restart (`fix-sqli-login/tests/test.sh:32-66`; `AGENTS.md:14-24`). DB state persists across runs; verifier wipes `appdb` before grading (`test.sh:40-44`; `AGENTS.md:32-36`).
- Network: no internet in eval (`instructions.md:68`); only `OPENAI_BASE_URL` endpoint reachable. Local `allow_internet=true` must not be relied on.
- Dependencies: nothing installable at runtime (`README.md:113`); fix tasks forbid new deps beyond `pyproject.toml` (`fix-sqli-login/instruction.md:7`). Submission ≤10 MB (`instructions.md:33`); use stdlib + preinstalled packages only.
- Interface: `run.sh` must accept the instruction as argv (≥1 arg) and not crash on spaces/newlines (flattened by `$*`); `agent.py` is overwritten so custom logic must live behind `run.sh`.

## 11. Failure Modes

Every observed or stated way to score 0:

- Contract: missing `run.sh` in zip (`instructions.md:35`; `README.md:87`); `run.sh` exiting 1 on empty prompt is fine but any crash/exception/timeout on a real prompt → 0 (`instructions.md:52-56`); depending on files outside the zip or on runtime `pip install` (`README.md:113`); requiring internet (`instructions.md:68`); >10 MB archive (`instructions.md:33`); CRLF-broken `run.sh` (mitigated by `.gitattributes:1`, but keep LF).
- Input mishandling: assuming workdir is `/app` (it is `REMOTE_DIR` initially — must `cd /app` or use absolute paths); assuming prompt newlines survive `$*`/`" ".join` (`agent/run.sh:12`; `agent/local_agent.py:317`).
- Output misses: wrong absolute path (`/app/hello.txt` vs relative); extra bytes beyond `Hello`/`Bye` (grader uses `cat`-equality, not substring); invalid JSON / missing `findings` / empty array (`test_security_report.py:25-30`); forensics file with ≠4 lines, blank lines, ` = ` spacing, extra keys, wrong order is OK (sorted before diff) but wrong values, non-verbatim timestamp, or CRLF edge cases (`incident-log-forensics/tests/test.sh:20-45`).
- Detection gaps: audit report mentioning SQLi but missing the login+detail keyword triples (`test_security_report.py:70-82`); fixing the wrong endpoint (each fix task has exactly one vuln — §9); incomplete parameterization (comment-bypass vs OR-bypass vs UNION-leak each tested separately); breaking any regression test (valid login, search, CRUD, comments/tags/users in `test_regression.py:1-78`).
- Runtime: leaving stale `uvicorn` with old code during self-check (use `pkill -f "uvicorn main:app"` + restart + `/healthz` poll per `AGENTS.md:18-24` and `solution/solve.sh:32-43`); assuming fresh DB (seed-once logic in `db.py:76-78`; stale rows persist — verifier recreates DB but agent's own checks must too); service not listening within 30s → verifier writes 0 (`test.sh:83-87`); app crash on startup (e.g. syntax error from bad `patch`) → 0.
- Forensics traps: using `audit.bytes` (18432) instead of `payload_logical_bytes` (2457600); using proxy/status size instead of logical bytes; picking decoy `legacy-bulk-77`/`soc-daily-archive-09`/`dup-export-internal` (wrong window/event/edge decision per `check_parity.py:151-170`); taking attacker IP from `auth.log`/`dns_ptr_hints.txt` instead of proxy XFF (`instruction.md:30`; `dns_ptr_hints.txt:3`); mishandling tab-continued proxy line, XFF `unknown`/private hops, trailing-comma XFF, or EDT→UTC conversion (see §9).
- Efficiency: solving but with bloated tokens/time loses ties (`instructions.md:61-64`).

## 12. Recommended MVP Agent

Small, deterministic, single-loop agent behind the existing `run.sh` contract. No swarms, RAG, or fine-tuning.

- Entry: keep `run.sh` semantics (`set -eu`, `LOCAL_AGENT_WORKDIR`, single prompt arg). First action in code: resolve task dir — `pwd; ls /app` — then branch on instruction keywords (`hello.txt|bye.txt` → trivial; `security_report.json` → audit; `pytest tests/` + FastAPI → fix; `incident_report.txt` → forensics; else generic).
- Loop: one LLM (local endpoint via `OPENAI_BASE_URL`/`OPENAI_API_KEY`/`LOCAL_AGENT_MODEL`) with ≤4 tools: `bash` (with timeout, cwd `/app`, 16k truncation), `read_file`, `apply_patch` (unified diff via `patch`, with fallback to python string-replace for small LLMs bad at diffs), `write_file` (full overwrite — add this; template only has append). Cap steps (e.g. dozens, well under `REQUEST_LIMIT=1000` in `local_agent.py:20`) and enforce a global deadline below the smallest agent timeout (120s) with margin.
- Per-class handlers (all shell-verifiable, no LLM judging):
  - Trivial: `printf 'Hello' > /app/hello.txt` (no LLM needed; short-circuit).
  - Audit: `rg -n "fetch(row|)|execute|f\".*SELECT|format\(|%s" /app --glob '*.py`; read `routers/auth.py`, `routers/items.py`; emit the reference-shaped JSON with login/SQLi/bypass keywords; validate with `python3 -m json.tool` + keyword grep before exit.
  - Fix: grep for `f-string`/`f"` SQL sinks, read the one hit, apply the known `$1/$2` parameterization (login) or `LIKE $1` with `f"%{q}%"` param (search), `pkill` stale uvicorn, restart, poll `/healthz` ≤30s, run `pytest tests/ -q`, retry once on failure.
  - Forensics: run a bundled `python3` correlator implementing `check_parity.py` logic (merge JSONLs, window+event+edge filter, max-magnitude/latest-ts, XFF public-IP extraction, tab-continuation join), write strict 4-line file, verify with `sort|diff` + line-count/`=` checks mirroring `tests/test.sh`.
- Robustness: every `bash` with timeout + exit-code capture; `set -u`-safe shell; absolute `/app` paths; LF-only writes; secret redaction in logs; final stdout summarizes changed files (template system prompt already asks for this in `local_agent.py:241-246`).

## 13. Potential Improvements

Ordered by practical value for a 40-hour, 2-person build (highest first, no scores):

- Full-overwrite `write_file` + diff-fallback patcher: template `apply_diff` needs exact unified diffs (`local_agent.py:122-150`), which small LLMs mangle; a python replace/overwrite path fixes most patch failures.
- Verifier-mirror self-checks per class (pytest + `/healthz` poll, JSON keyword check, forensics `sort|diff` check): catches failures before exit using the same assertions as `tests/test.sh`.
- Stale-service + DB-reset helpers (`pkill`, `service postgresql start`, drop/create `appdb`, 30s health poll per `fix-sqli-login/tests/test.sh:32-87`): removes the largest local flake source documented in `AGENTS.md:14-36`.
- Task router by instruction keywords with deterministic fast paths for trivial/audit/forensics shapes: saves tokens/time vs full agentic loop on easy tasks.
- Minimal SQLi-fix playbook (only `$n` parameterization patterns from `solution/solve.sh` files): small LLMs succeed at one idiom; avoid generic "find all vulns" prompting.
- Forensics correlator script vendored in submission (port of `scripts/check_parity.py:137-213` without the expected-answer comparison): turns multi-log reasoning into code execution.
- Audit report template pre-filled with login/SQLi/bypass vocabulary matching `test_security_report.py:37-68`: guarantees the keyword triple without relying on LLM wording.
- Token/time budgeting (short system prompt, truncate tool output at 16k already in `local_agent.py:18`, cap steps, early exit on green self-check): directly serves the efficiency tie-break (`instructions.md:61-64`).
- Retry-with-backoff on LLM/HTTP flakes and `curl`-based endpoint probes before declaring a fix complete.
- Only then: broader detectors (semgrep/`rg` rules for XSS/SSRF/IDOR), multi-payload self-attack (`admin'--`, `OR '1'='1`, UNION SELECT), or CTF helpers (flag grep, `strings`, base64/jwt decode) — valuable only after the MVP loop is green on all six local tasks.

## 14. Unknowns

- Closed benchmark composition: 15 tasks announced (`instructions.md:20`) vs 6 runnable local tasks + 1 source tree; distribution across vuln-detection/forensics/SWE-fix/CTF, difficulty mix, and whether trivial file tasks appear in eval are unstated.
- CTF shape: no local CTF example; flag format, submission mechanism (file? service exploit? stdout?), and tooling needs are unknown.
- Per-task token/time limits in eval: announced (`instructions.md:20`) but values absent from local `task.toml` (only `timeout_sec` for agent/verifier); enforcement (kill vs truncate vs penalty) unknown.
- Eval model identity and capability (context length, tool-use reliability, reasoning depth): only "small local LLM" (`instructions.md:20`; `README.md:33-37`); local `-m qwen/qwen3.6-35b-a3b` (`README.md:81`) is dev-only.
- Filesystem visibility in eval: whether `/tests`, `/logs/verifier` exist or are readable by the agent (local verifiers live outside `/app` at `/tests`, `/logs/verifier/*`); whether agent may read its own `local-agent.txt`/`setup.log`.
- Working directory at eval: `REMOTE_DIR` per `agent/agent.py:67` vs `/app` per instructions — confirmed divergent; whether eval sets `LOCAL_AGENT_WORKDIR=/app` is not in repo.
- Network egress scope: "no internet" (`instructions.md:68`) — whether localhost/postgres/service ports, DNS, or the LLM endpoint hostname are the only allowlisted destinations is unspecified.
- Resource caps in eval (CPU/RAM/process count/file size): local values in §8 may not transfer; OOM/kill behavior unknown.
- Scoring harness version: local Harbor pin `harbor==0.16.1` (`README.md:131`) and `schema_version="1.2"` may differ in closed eval; `reward.txt` path convention is inferred from local `test.sh` files only.
- Submission mechanics: upload endpoint, checkpoint cutoff enforcement (`instructions.md:77-123`), and whether multiple `run.sh`-adjacent files/languages/binaries are allowed within 10 MB are procedural unknowns.
- `AGENTS.md` presence in eval: local FastAPI tasks all ship it, but closed tasks may not; agent must not depend on it.
- `insecure-api-app` role in eval: dev-only sync source (`sync.sh:1-55`) or indicative of additional hidden SQLi variants — unclear.
