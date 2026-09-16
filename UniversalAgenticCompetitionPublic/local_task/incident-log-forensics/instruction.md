# IR-2026-0501 — Data exfil suspicion (api-3)

Security operations opened a ticket after DLP noise on **api-3** around **May 1, 2026**. Disk sync during containment **truncated** the primary application audit file mid-incident; a **SIEM/WORM fragment** was later attached. 

You are the analyst on duty. Review everything under **`/app/incident/`**, reconcile the story, and record your **attributed primary exfiltration** conclusion in **`/app/incident_report.txt`**.

**Artifacts (read all that exist in the directory):**

- `collector_note.txt` — what broke on disk and how fragments were recovered.
- `app.jsonl` / `app_audit_recovered.jsonl` — nested JSONL application audit.
- `proxy_access.log` — load-balanced HTTP access
- `edge_decisions*.log` — SOC edge disposition export (may be split across shards; e.g. `edge_decisions.log` plus `edge_decisions_fragment.log`);
- `dns_ptr_hints.txt` — optional passive-DNS / PTR context only;
- `auth.log` — `sshd` on **prod-auth-01**

**Deliverable — strict machine format**

Write **`/app/incident_report.txt`**: UTF-8, **exactly four** non-empty lines, **one** `key=value` per line, **no** spaces around `=`, **no** blank lines, **no** commentary. Each of the following keys must appear **once**:

- `attacker_ip`
- `compromised_user`
- `exfil_bytes`
- `first_malicious_event_utc`

**Report fields (normative mapping)** 

- `compromised_user` = that record's `identity.subject`.
- `exfil_bytes` = that record's `audit.payload_logical_bytes` if present; otherwise `audit.bytes`.
- `first_malicious_event_utc` = that record's `ts` copied **verbatim** (ISO 8601 UTC, including fractional seconds).
- `attacker_ip` = derived from `proxy_access.log` for the matched HTTP request using the XFF.

Do not add keys, rename keys, or embed explanations in the deliverable file.
