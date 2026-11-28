# Rules

- Sacrifice grammar for concision. Exception: when asked for detail, prioritize clarity.
- This repo is **public**. Never commit host names, IPs, ports, running versions, scan output or vulnerabilities here. Never commit secrets.
- Sensitive docs (inventory, findings, exceptions register, raw scans) and the issue tracker live in the private repo **`Sacon217/home-lab-ops`** (clone: `~/GitHub/home-lab-ops`). Read its `docs/agents/issue-tracker.md` and `docs/agents/triage-labels.md` before touching issues.
- Every `gh issue` call carries `-R Sacon217/home-lab-ops`. A PreToolUse hook (`.claude/hooks/block-public-issue-writes.sh`) blocks issue writes anywhere else. Never work around it.
- Issues stay enabled here only for Renovate (Dependency Dashboard, config-error alerts).
- All documentation lives in `home-lab-ops`. The agent never adds documentation to this repo; what is published here is the user's call.
- The user runs remediation actions on the hosts; the agent guides, researches, reviews and documents.
- No code comments in code the agent writes (scripts, YAML, Dockerfiles, compose, Python). Names and docs carry the explanation; shebangs stay.
- No AI attribution anywhere: no co-author trailers, no "generated with" lines, no Anthropic noreply address in commits, PR bodies, issues or files. Enforced by `.githooks/commit-msg` (run `git config core.hooksPath .githooks` after cloning) and the `no-ai-attribution` PR check.
