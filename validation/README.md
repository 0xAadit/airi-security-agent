# Validation harnesses (WSL/Linux)

Copied from the Windows/WSL validation phase. They emulate the Harbor contract
(real `/app` fixtures, real `sh run.sh "<instruction>"`, real per-task `tests/test.sh`)
without Docker.

- `bench2.sh` — hello/bye/incident/find-sqli via real `test.sh` + fix-task static checks.
- `bench3.sh` — fix tasks against live postgres (regression + payload probes).
- `bench4.sh` — fix verifier mirror (exact hidden-equivalent suites, fresh DB + restarted server).
- `inspect.sh` — sandbox diagnostics.

On Arch, update the `REPO=` path (currently `/mnt/d/...`) to the local checkout and
ensure `python3`, `pytest`, and (for bench3/4) `postgresql` + app deps are installed.
Logs should go to a persistent directory (WSL `/tmp` is tmpfs and wiped between sessions).
