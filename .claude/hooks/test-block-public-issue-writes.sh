#!/usr/bin/env bash
# Tests for block-public-issue-writes.sh. Run: bash .claude/hooks/test-block-public-issue-writes.sh
set -u
HOOK="$(dirname "$0")/block-public-issue-writes.sh"
pass=0; fail=0

decide() {
  local out
  out=$(jq -n --arg c "$1" '{tool_name:"Bash",tool_input:{command:$c}}' | bash "$HOOK" 2>/dev/null)
  if printf '%s' "$out" | jq -e '.hookSpecificOutput.permissionDecision=="deny"' >/dev/null 2>&1; then
    echo deny
  else
    echo allow
  fi
}

check() {
  local want=$1 cmd=$2 got
  got=$(decide "$cmd")
  if [ "$got" = "$want" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: want $want, got $got :: $cmd"; fi
}

[ -f "$HOOK" ] || { echo "FAIL: hook missing at $HOOK"; exit 1; }

# Writes that must be denied
check deny  'gh issue create --title x'
check deny  'gh issue comment 5 -R Sacon217/home-lab'
check deny  'gh issue edit 1 --repo=Sacon217/home-lab'
check deny  'gh issue close 2 -RSacon217/home-lab'
check deny  'gh issue create -R Sacon217/home-lab-ops-x --title x'
check deny  'gh issue list; gh issue create --title x'
check deny  'gh issue create -R Sacon217/home-lab-ops --title a && gh issue create --title b'
check deny  'gh api --method POST repos/Sacon217/home-lab/issues -f title=x'
check deny  'gh api -X PATCH repos/Sacon217/home-lab/issues/1'

# Must stay allowed
check allow 'gh issue create -R Sacon217/home-lab-ops --title x'
check allow 'gh issue comment 3 --repo=Sacon217/home-lab-ops -b y'
check allow 'gh issue edit 4 --repo Sacon217/home-lab-ops --add-label ready'
check allow 'gh issue list'
check allow 'gh issue view 3'
check allow 'gh api repos/Sacon217/home-lab/issues'
check allow 'gh api --method POST repos/Sacon217/home-lab-ops/issues/1/sub_issues -F sub_issue_id=2'
check allow 'gh pr create --fill'
check allow 'echo gh issue'
check allow 'git status'

echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
