import json
from pathlib import Path
from typing import Any


REPORT_PATH = Path("/app/security_report.json")


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_flatten(v) for v in value)
    return str(value)


def _has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def test_security_report_exists():
    assert REPORT_PATH.exists(), f"Expected report at {REPORT_PATH}"


def test_security_report_is_valid_json_object():
    data = json.loads(REPORT_PATH.read_text())
    assert isinstance(data, dict), "Report must be a top-level JSON object"
    assert "findings" in data, "Report must contain a top-level 'findings' field"
    assert isinstance(data["findings"], list), "'findings' must be a JSON array"
    assert data["findings"], "'findings' must contain at least one finding"


def test_report_contains_login_sql_injection_finding():
    data = json.loads(REPORT_PATH.read_text())
    findings = data.get("findings", [])

    sql_injection_signals = [
        "sql injection",
        "sqli",
        "sql_injection",
        "cwe-89",
        "injection",
        "raw sql",
        "string interpolation",
        "f-string",
        "parameterized",
        "prepared statement",
    ]
    login_signals = [
        "login",
        "/login",
        "auth",
        "authentication",
        "routers/auth.py",
        "auth.py",
        "loginrequest",
    ]
    detail_signals = [
        "bypass",
        "authentication bypass",
        "admin'--",
        "or '1'='1",
        "password",
        "credential",
        "req.username",
        "req.password",
        "fetchrow",
    ]

    matching_findings = []
    for finding in findings:
        text = _flatten(finding).lower()
        has_sqli = _has_any(text, sql_injection_signals)
        has_login = _has_any(text, login_signals)
        has_detail = _has_any(text, detail_signals)
        if has_sqli and has_login and has_detail:
            matching_findings.append(finding)

    assert matching_findings, (
        "Expected at least one finding describing SQL injection in the login/authentication flow "
        "with concrete evidence, impact, or exploit detail"
    )
