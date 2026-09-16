You are working in `/app`. The application is a FastAPI service backed by PostgreSQL.

Perform a security audit of the application as if preparing a bug bounty report.

Do not modify application code. Your deliverable is a machine-readable JSON report at:

`/app/security_report.json`

The report must be valid JSON with this top-level shape:

```json
{
  "findings": [
    {
      "title": "Short finding title",
      "severity": "critical|high|medium|low|informational",
      "category": "Vulnerability category",
      "location": "Affected file, function, endpoint, or component",
      "evidence": "Concrete code or behavior that demonstrates the issue",
      "impact": "Security impact",
      "recommendation": "Recommended remediation"
    }
  ]
}
```

Include enough detail for each finding to be useful to an engineer triaging a bug bounty report.
