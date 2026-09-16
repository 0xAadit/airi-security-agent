# LLM Runtime Checklist

Agent: `UniversalAgenticCompetitionPublic/agent/local_agent.py` (stdlib only) via `run.sh`.
Status: LLM loop NOT yet validated against a live endpoint — smoke mode reports `skip` here.

## 1. Exact LLM request format

- `POST {OPENAI_BASE_URL}/chat/completions` (trailing `/` stripped before appending path).
- Headers: `Content-Type: application/json`, `Authorization: Bearer {OPENAI_API_KEY}`.
- Body: `{"model": ..., "messages": [{"role": "system|user|assistant", "content": str}],
  "temperature": 0.2, "max_tokens": 1200}`.
- Transport: stdlib `urllib`, per-call timeout 45s. No streaming, no function-calling API,
  no extra SDKs. Compatible with any OpenAI-style endpoint (local vLLM/Ollama-gateway/OpenRouter).

## 2. Environment variables

| Var | Required for | Behavior if missing |
|-----|--------------|---------------------|
| `LOCAL_AGENT_MODEL` (or `OPENAI_MODEL` fallback) | LLM loop | LLM skipped, deterministic fallbacks only |
| `OPENAI_BASE_URL` | LLM loop | LLM skipped |
| `OPENAI_API_KEY` | LLM loop | LLM skipped |
| `LOCAL_AGENT_WORKDIR` | workdir (set by `run.sh`) | falls back to process cwd |

Missing creds never crash: agent logs `llm_skipped` and continues deterministically, exit 0.

## 3. Expected response format

- `choices[0].message.content` as string (empty/null content treated as `""`).
- Optional `usage: {prompt_tokens, completion_tokens, total_tokens}` accumulated into
  `LLM_USAGE` and logged as `llm_usage` (missing usage tolerated — tie-break accounting best-effort).
- Anything else raises `RuntimeError("bad LLM response shape")` → loop breaks to fallbacks.

## 4. Tool protocol

- One tool per step, exactly: ` ```json {"tool": "<name>", "args": {...}} ``` `.
- Tools: `bash{command,timeout?}`, `read_file{path}`, `list_dir{path}`,
  `search{pattern,path?,include?}`, `write_file{path,content}`,
  `apply_patch{path,old_text,new_text}`, `append_file{path,content}`.
- Finish only with `FINAL: <summary>` (case-insensitive) AFTER verifying artifacts.
- Unknown tool / non-dict args / tool crash → recovered message, loop continues.
- Unparseable reply → one format nudge, then give up near iteration cap (no infinite retry).

## 5. Failure cases

- No creds → skip LLM, deterministic paths (verified locally for all 6 tasks).
- HTTP/timeout/shape error → break loop, run self-check + deterministic fallback.
- `content: null` (tool-call-style servers) → parsed as `""` → nudge path.
- Stale-server pytest signal → self-check fails honestly (pipe-masking bug fixed: list-form
  subprocess, pass requires `rc==0 AND "passed" in output`).
- Every dispatch/tool/parse/verify step is exception-guarded; `main()` always exits 0.

## 6. Timeout strategy

- bash tool: 30s default, 60s max. LLM call: 45s. pytest probes: 60s.
- Global budget: 90s trivial / 500s other (evaluator allows 120s / 600s).
- Loop exits when <20s remain. Worst case ≈ 480s loop + 60s check + 60s fallback probe < 600s.

## 7. Token strategy

- Small-model-first: short system prompt + one-line class hint, `temperature 0.2`.
- Cap 1200 completion tokens/call; observations truncated to 8000 chars.
- Sliding history: system + task + last 8 messages (small-context safe).
- Zero-token fast paths: trivial file-write and forensics correlator run before any LLM call.
- Usage accumulated per run when the server reports it; efficiency tie-break is secondary to solving.

## 8. Docker compatibility checks (verified)

- [x] stdlib imports only (`argparse json logging os re subprocess sys time urllib datetime pathlib`).
- [x] Single network egress: the LLM POST above; everything else is local files/processes.
- [x] `run.sh` LF, `set -eu`, passes prompt as one arg; agent joins argv (whitespace-flatten safe).
- [x] Prefers `/app` when present, else workdir; absolute `/app` paths everywhere in prompts/tools.
- [x] `pathlib.write_text(newline=...)` is 3.10+ API — fine on 3.12.
- [x] POSIX-only shell usage (`rg`→`grep`→pure-python search fallback); no Windows-only APIs.
- [x] No background processes leaked by agent code; verifier owns service restarts.
- [x] Submission footprint ~52KB (`run.sh` + `local_agent.py`), far under 10MB.

## 9. Smoke test

```sh
python3 local_agent.py --smoke-test   # temp dir only, never touches /app
```

Prints JSON: `{"status": "pass"|"fail"|"skip", "latency_s": ..., "usage": {...}, ...}`.
`skip` (no creds) is the honest result in this sandbox. `pass` requires a live endpoint
and proves: request format accepted, one real tool dispatch, `FINAL` parsed, usage read.

## 10. Real benchmark requirements (not met here)

- Linux host with Docker + `secureintelligent/acp` image + `harbor` (+ `uv`).
- Reachable LLM endpoint + `OPENAI_API_KEY`; model name via `-m` (becomes `LOCAL_AGENT_MODEL`).
- Then run the six local tasks in order (hello, bye, find-sqli, fix-login, fix-search, forensics),
  capture reward/runtime/LLM calls/tokens per task, and only then optimize further.
