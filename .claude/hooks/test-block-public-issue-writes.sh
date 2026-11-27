#!/usr/bin/env bash
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

check deny  'gh issue create --title x'
check deny  'gh issue comment 5 -R Sacon217/home-lab'
check deny  'gh issue edit 1 --repo=Sacon217/home-lab'
check deny  'gh issue close 2 -RSacon217/home-lab'
check deny  'gh issue create -R Sacon217/home-lab-ops-x --title x'
check deny  'gh issue list; gh issue create --title x'
check deny  'gh issue create -R Sacon217/home-lab-ops --title a && gh issue create --title b'
check deny  'gh api --method POST repos/Sacon217/home-lab/issues -f title=x'
check deny  'gh api -X PATCH repos/Sacon217/home-lab/issues/1'

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

check allow 'gh issue comment 3 -R Sacon217/home-lab-ops --body "Fixed with chmod -R 750 /srv/data"'
check allow "gh issue comment 3 -R Sacon217/home-lab-ops --body 'grep -R foo /etc'"
check deny  'gh issue create --title x --body " -R Sacon217/home-lab-ops"'
check allow 'gh issue create -R "Sacon217/home-lab-ops" --title x'
check allow 'gh issue create --title "a; b | c" -R Sacon217/home-lab-ops'

check allow $'gh issue create \\\n  -R Sacon217/home-lab-ops \\\n  --title x'
check deny  $'gh api repos/Sacon217/home-lab/issues \\\n  --method POST -f title=x'
check deny  $'gh issue list\ngh issue create --title x'

check deny  "bash -c 'gh issue create --title x'"
check deny  'sh -c "gh issue comment 1 -R Sacon217/home-lab -b x"'
check deny  'echo "$(gh issue create --title x)"'
check deny  'echo `gh issue create --title x`'
check deny  'eval "gh issue create --title x"'
check deny  $'bash <<\'EOF\'\ngh issue create --title x\nEOF'
check deny  '"gh" issue create --title x'
check deny  'ls | xargs gh issue create --title x'
check allow "bash -c 'gh issue create -R Sacon217/home-lab-ops --title x'"

check deny  'gh issue new --title x'
check deny  'gh issue -R Sacon217/home-lab create --title x'
check allow 'gh issue -R Sacon217/home-lab-ops create --title x'
check allow 'gh issue edit 4 -R sacon217/home-lab-ops --add-label ready'

check deny  'gh api --method=POST repos/Sacon217/home-lab/issues -f title=x'
check deny  'gh api -XPOST repos/Sacon217/home-lab/issues'
check deny  'gh api repos/Sacon217/home-lab/issues -ftitle=x'
check deny  'gh api repos/Sacon217/home-lab/issues --raw-field title=x'
check deny  'gh api repos/{owner}/{repo}/issues -f title=x'
check deny  'gh api repos/sacon217/HOME-LAB/issues -f title=x'
check deny  "gh api graphql -f query='mutation{createIssue(input:{repositoryId:\"x\",title:\"y\"}){issue{number}}}'"
check allow 'gh api -X GET repos/Sacon217/home-lab/issues -f state=all'
check allow 'gh api repos/Sacon217/home-lab-ops/issues -f title=x'
check allow "gh api graphql -f query='query{viewer{login}}'"

check deny  'gh api -X POST /repos/Sacon217/home-lab/issues -f title=x'
check deny  'gh api -X POST https://api.github.com/repos/Sacon217/home-lab/issues -f title=x'
check deny  'gh api --method PATCH "/repos/Sacon217/home-lab/issues/1" -f state=closed'
check allow 'gh api -X POST /repos/Sacon217/home-lab-ops/issues -f title=x'

check allow 'git commit -m "hook blocks gh issue create without -R"'
check allow $'git commit -F - <<\'EOF\'\nmention gh issue create here\nEOF'
check allow $'gh pr create --title t --body "$(cat <<\'EOF\'\nblocks gh issue create\nEOF\n)"'

echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
