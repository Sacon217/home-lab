#!/usr/bin/env bash
set -uo pipefail
pattern='co-authored-by:[[:space:]]*claude|noreply@anthropic\.com|generated with \[?claude code|claude\.com/claude-code'
if grep -Eiq "$pattern"; then
  echo "Blocked: AI attribution found (co-author trailer, generated-with line or Anthropic noreply address). Remove it." >&2
  exit 1
fi
exit 0
