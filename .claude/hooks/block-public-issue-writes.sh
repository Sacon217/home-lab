#!/usr/bin/env bash
# PreToolUse hook (Bash): issue writes may only target the private tracker Sacon217/home-lab-ops.
# This repo is public; a security finding filed here is free recon for anyone.
# Tests: bash .claude/hooks/test-block-public-issue-writes.sh
set -uo pipefail

TRACKER='Sacon217/home-lab-ops'

cmd=$(jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0
[ -n "$cmd" ] || exit 0

deny() {
  jq -n --arg r "$1" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $r
    }
  }'
  exit 0
}

gh_prefix='(^|[[:space:](])([^[:space:]]*/)?gh[[:space:]]+'
issue_writes='create|edit|comment|close|reopen|delete|transfer|pin|unpin|lock|unlock|develop'

# Judge each segment of a compound command on its own.
segments=$(printf '%s\n' "$cmd" | sed -E 's/(&&|\|\||;|\|)/\n/g')

while IFS= read -r seg; do
  if printf '%s' "$seg" | grep -Eq "${gh_prefix}issue[[:space:]]+(${issue_writes})([[:space:]]|\$)"; then
    repo=$(printf '%s' "$seg" | grep -oE '(^|[[:space:]])(-R|--repo)(=|[[:space:]]*)[^[:space:]]+' | tail -1 |
      sed -E 's/^[[:space:]]*(-R|--repo)(=|[[:space:]]*)//; s/^["'\'']//; s/["'\'']$//')
    if [ "$repo" != "$TRACKER" ]; then
      deny "Blocked: 'gh issue' write must target the private tracker with -R ${TRACKER} (got '${repo:-none}'). This repo is public. See CLAUDE.md."
    fi
  fi

  if printf '%s' "$seg" | grep -Eq "${gh_prefix}api([[:space:]]|\$)" &&
     printf '%s' "$seg" | grep -Eq 'repos/Sacon217/home-lab/issues' &&
     printf '%s' "$seg" | grep -Eq '(--method|-X)[[:space:]]*(POST|PATCH|PUT|DELETE)|[[:space:]](-f|-F|--field|--raw-field|--input)[[:space:]]'; then
    deny "Blocked: gh api write against issues of the public repo Sacon217/home-lab. Use ${TRACKER}. See CLAUDE.md."
  fi
done <<< "$segments"

exit 0
