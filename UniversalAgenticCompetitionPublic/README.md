# Universal Agent Competition: Cybersecurity - Public

This repository is the public part of the competition. It contains a small set of local example tasks and a simple example agent that can run on them.

The goal is to show the shape of the tasks and the shape of an agent submission. This is not meant to be a strong baseline agent.

This repository is not the final benchmark. The tasks in `local_task/` are provided for local development and validation only. Official scoring will use a closed set of evaluation tasks.

## Updates

2026-08-26: Enforced LF line endings for shell scripts and incident report fixtures, and made incident report verification tolerant of CRLF input.

2026-07-09: Fixed `fix-sqli-search` and `fix-sqli-login` reference solutions to match current source files and wait for the local service before running regression tests.

2026-07-08: Fixed local task fixtures and entrypoint startup for SQL injection and incident log tasks.

2026-07-08: Fixed example local agent stream event handling for current `pydantic-ai` APIs, including async context-managed streams and tool result event shape changes; updated `sample_submission.zip` accordingly.

## Competition focus

The main focus of this competition is cybersecurity-oriented agent tasks. We strongly recommend participants review the following materials for security context:

- [MITRE ATT&CK](https://attack.mitre.org/)
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)

Submissions will be evaluated on tasks such as:

- finding vulnerabilities in code
- digital forensics tasks
- fixing cybersecurity issues in SWE-bench-style tasks
- CTF-style tasks

The core objective is to build a universal agent that remains useful under constrained settings and can work effectively with small LLMs.

Why this matters: cybersecurity specialists often work with sensitive data and proprietary source code that cannot be sent to public LLM providers. In many environments, internet access is also restricted or fully unavailable.

In such conditions, local LLMs are the only practical option. This competition exists to push forward methods and agents that can solve real cybersecurity tasks effectively and autonomously with small local language models.

## Scoring and leaderboard

Each task is evaluated separately and receives a binary score: `0` (failed) or `1` (solved).

Each task has its own token and time limits.

Leaderboard ranking is based on solved task count first. If two agents solve the same number of tasks, the faster and more token-efficient agent gets the higher rank.

## What is inside

`local_task/` contains example tasks. Each task has its own folder with the task config, environment, instructions, tests, and sometimes a reference solution.

`agent/` contains an example agent submission. It shows how a participant package should be structured and how Harbor will call the agent.

Important files in `agent/`:

`agent/agent.py` is the Harbor wrapper. It defines `class MyInstalledAgent(BaseInstalledAgent)`. This file is part of the required interface and should be the same for all participants.

`agent/run.sh` is the entry point for the participant's agent. Harbor runs this script inside the task environment and passes the task instruction as an argument.

`agent/local_agent.py` is just one example implementation. Participants can replace this with their own code, or call any other program from `run.sh`.

## Running locally

Set your OpenRouter credentials first:

```sh
export OPENAI_API_KEY=your_key_here
```

Then run the local tasks with the example agent:

```sh
uv run harbor run -p local_task --agent-import-path agent.agent:MyInstalledAgent -m qwen/qwen3.6-35b-a3b --ae OPENAI_API_KEY=$OPENAI_API_KEY --ae OPENAI_BASE_URL=https://openrouter.ai/api/v1 -y
```

The command tells Harbor to:

`-p local_task` use the local example tasks.

`--agent-import-path agent.agent:MyInstalledAgent` load the installed agent wrapper from `agent/agent.py`.

`-m qwen/qwen3.6-35b-a3b` pass this model name to the agent.

`--ae ...` pass environment variables to the agent.

## Submission format

A participant submission must be a `.zip` archive with agent files. At minimum it must contain `run.sh`.

See [`sample_submission.zip`](./sample_submission.zip) for an example submission layout.

At minimum it must contain:

```text
  run.sh
  // Anything else excpet agent.py - this file will be automatically added to your submission for run it. If it will present, it will overwritten by same agent.py as you can find in repo.
```

`agent/agent.py` will contain `class MyInstalledAgent(BaseInstalledAgent)`. For this competition, this wrapper will stay the same for everyone.

Your actual agent logic should be started from `run.sh`. You can put extra files next to it, for example Python files, configs, or scripts. The example here uses `local_agent.py`, but your submission can use a different implementation.


## Submission runtime constraints

Submissions are executed in an isolated microVM without internet access.

Only a local LLM endpoint is available. Connection details are provided through:

- `LOCAL_AGENT_MODEL`
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`

Installing additional dependencies at runtime is not possible. Your submission must work with only the source files you include.

For local validation, use the same environment image: [secureintelligent/acp:latest](https://hub.docker.com/r/secureintelligent/acp)

`secureintelligent/acp` runtime image (Python 3.12) with Harbor, agent SDKs, and common CLI/network tooling.

Installed packages in acp:
```
requires-python = ">=3.12"
dependencies = [
    "aiohttp>=3.13.4",
    "anthropic>=0.97.0",
    "claude-agent-sdk>=0.1.72",
    "cohere>=6.1.0",
    "crewai>=1.6.1",
    "google-genai>=1.74.0",
    "groq>=1.2.0",
    "harbor==0.16.1",
    "httpx>=0.28.1",
    "langchain>=1.2.17",
    "langchain-anthropic>=1.4.3",
    "langchain-community>=0.4.1",
    "langchain-core>=1.3.2",
    "langchain-openai>=1.1.10",
    "langgraph>=1.1.10",
    "litellm>=1.83.14",
    "llama-index>=0.14.21",
    "mistralai>=2.4.4",
    "openai>=2.24.0",
    "openai-agents>=0.10.5",
    "pydantic-ai>=1.44.0",
    "python-dotenv>=1.2.2",
    "tenacity>=9.1.4",
    "tiktoken>=0.12.0",
]
```

### Installed packages

**System tools (APT, preinstalled)**

- `build-essential`, `cmake`, `curl`, `git`, `jq`, `openssl`, `ripgrep`, `tcpdump`, `traceroute`, `tree`, `unzip`, `wget`, `zip`, and other standard debugging/network utilities.

**Python packages (locked from `uv.lock`)**

- Core stack includes `harbor`, `openai`, `anthropic`, `google-genai`, `litellm`, `langchain`, `langgraph`, `llama-index`, `openai-agents`, and related SDK dependencies.

When Harbor starts a task, it installs the `agent/` directory into the environment, makes `run.sh` executable, and runs:

```sh
./run.sh "<task instruction>"
```
