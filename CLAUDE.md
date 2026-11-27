# Rules

- Sacrifice grammar for concision. Exception: when asked for detail, prioritize clarity.
- This repo is **public**. Never commit host names, IPs, ports, running versions, scan output or vulnerabilities here. Never commit secrets.
- Sensitive docs (inventory, findings, exceptions register, raw scans) and the issue tracker live in the private repo **`Sacon217/home-lab-ops`** (clone: `~/GitHub/home-lab-ops`). Read its `docs/agents/issue-tracker.md` and `docs/agents/triage-labels.md` before touching issues.
- Every `gh issue` call carries `-R Sacon217/home-lab-ops`. A PreToolUse hook (`.claude/hooks/block-public-issue-writes.sh`) blocks issue writes anywhere else. Never work around it.
- Issues stay enabled here only for Renovate (Dependency Dashboard, config-error alerts).
- `docs/` here is the sanitized, public write-up: methodology, generic runbooks, CIS mapping.
- The user runs remediation actions on the hosts; the agent guides, researches, reviews and documents.
