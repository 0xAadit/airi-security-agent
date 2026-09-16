#!/usr/bin/env python3
"""Recompute the four report fields from bundle files; exit 0 iff they match tests/expected."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

WINDOW_START = datetime(2026, 5, 1, 14, 3, 0, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 5, 1, 14, 4, 59, 999_999, tzinfo=timezone.utc)


def strip_ascii_ws(s: str) -> str:
    return s.strip(" \t\n\r\x0b\x0c")


def ipv4_from_segment(seg: str) -> str | None:
    seg = strip_ascii_ws(seg)
    if not seg or seg == "-":
        return None
    parts = seg.split(".")
    if len(parts) != 4:
        return None
    try:
        octets = [int(p) for p in parts]
    except ValueError:
        return None
    if any(o < 0 or o > 255 for o in octets):
        return None
    return ".".join(str(o) for o in octets)


def is_private_ipv4(ip: str) -> bool:
    a, b, _c, _d = (int(x) for x in ip.split("."))
    if a == 10:
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    if a == 192 and b == 168:
        return True
    return False


def xff_public_client(xff_inner: str) -> str:
    raw = xff_inner.split(",")
    hops: list[str] = []
    for p in raw:
        ip = ipv4_from_segment(p)
        if ip:
            hops.append(ip)
    for ip in reversed(hops):
        if not is_private_ipv4(ip):
            return ip
    raise RuntimeError(f"no public hop in {xff_inner!r}")


def merge_proxy_physical(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if line.startswith("#"):
            continue
        if not line.strip():
            continue
        if line[0] == "\t" and out:
            out[-1] = out[-1] + line
        else:
            out.append(line)
    return out


def parse_access(logical: str) -> tuple[int, int, str | None, str | None]:
    m_status = re.search(r'" (\d{3}) (\d+) ', logical)
    if not m_status:
        raise RuntimeError(f"no status/size in {logical[:120]!r}")
    status, size = int(m_status.group(1)), int(m_status.group(2))
    m_rid = re.search(r"rid=([^\s]+)", logical)
    rid = strip_ascii_ws(m_rid.group(1)) if m_rid else None
    m_xff = re.search(r'xff="([^"]*)"', logical)
    xff = m_xff.group(1) if m_xff else None
    return status, size, rid, xff


def edge_confirm_rids(edge_text: str) -> set[str]:
    confirmed: set[str] = set()
    for line in edge_text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if "CONFIRM_SENSITIVE" not in line:
            continue
        if "request_id=" not in line or " decision=" not in line:
            continue
        i = line.index("request_id=") + len("request_id=")
        j = line.index(" decision=", i)
        confirmed.add(strip_ascii_ws(line[i:j]))
    return confirmed


def edge_confirm_rids_from_env(env: Path) -> set[str]:
    confirmed: set[str] = set()
    for path in sorted(env.glob("edge_decisions*.log")):
        confirmed |= edge_confirm_rids(path.read_text(encoding="utf-8"))
    return confirmed


def parse_ts_z(s: str) -> datetime:
    if not s.endswith("Z"):
        raise ValueError(s)
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def magnitude(row: dict) -> int:
    audit = row["audit"]
    if "payload_logical_bytes" in audit:
        return int(audit["payload_logical_bytes"])
    return int(audit["bytes"])


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def load_merged_application_rows(env: Path) -> list[dict]:
    base = load_jsonl(env / "app.jsonl")
    base.extend(load_jsonl(env / "app_audit_recovered.jsonl"))
    return base


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    env = root / "environment"
    expected_path = root / "tests" / "expected_incident_report.txt"
    if len(sys.argv) > 1:
        env = Path(sys.argv[1])

    proxy = merge_proxy_physical(
        env.joinpath("proxy_access.log").read_text(encoding="utf-8").splitlines()
    )
    app = load_merged_application_rows(env)
    app.sort(key=lambda r: parse_ts_z(r["ts"]))
    confirmed = edge_confirm_rids_from_env(env)

    candidates: list[dict] = []
    for row in app:
        ts = parse_ts_z(row["ts"])
        if not (WINDOW_START <= ts <= WINDOW_END):
            continue
        if row.get("audit", {}).get("event") != "sensitive_export":
            continue
        rid = strip_ascii_ws(row["http"]["request_id"])
        if rid not in confirmed:
            continue
        candidates.append(row)

    if not candidates:
        print("no candidates", file=sys.stderr)
        return 2

    max_mag = max(magnitude(r) for r in candidates)
    tied = [r for r in candidates if magnitude(r) == max_mag]
    winner = max(tied, key=lambda r: parse_ts_z(r["ts"]))

    rid = strip_ascii_ws(winner["http"]["request_id"])
    audit_bytes = int(winner["audit"]["bytes"])
    has_transport = "transport" in winner.get("audit", {})

    attacker: str | None = None
    for logical in proxy:
        status, size, prid, xff = parse_access(logical)
        if prid != rid or xff is None:
            continue
        if has_transport:
            if status != 200 or size != audit_bytes:
                continue
        attacker = xff_public_client(xff)
        if has_transport:
            break

    if attacker is None:
        print("no attacker", file=sys.stderr)
        return 3

    exfil = magnitude(winner)
    compromised = winner["identity"]["subject"]
    first_ts = winner["ts"]

    got = {
        "attacker_ip": attacker,
        "compromised_user": compromised,
        "exfil_bytes": str(exfil),
        "first_malicious_event_utc": first_ts,
    }

    exp_lines = expected_path.read_text(encoding="utf-8").strip().splitlines()
    exp: dict[str, str] = {}
    for ln in exp_lines:
        k, v = ln.split("=", 1)
        exp[k] = v

    if got != exp:
        print("MISMATCH", file=sys.stderr)
        print("got:", got, file=sys.stderr)
        print("exp:", exp, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
