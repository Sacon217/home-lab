#!/usr/bin/env bash
set -u
CHECK="$(dirname "$0")/check-attribution.sh"
pass=0; fail=0
check() {
  local want=$1 text=$2 got
  if printf '%s' "$text" | bash "$CHECK" >/dev/null 2>&1; then got=clean; else got=blocked; fi
  if [ "$got" = "$want" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: want $want, got $got :: $text"; fi
}
[ -f "$CHECK" ] || { echo "FAIL: checker missing at $CHECK"; exit 1; }
T1='Co-Authored-By'; T1l='co-authored-by'; T2='Generated with'; T3='noreply@anthropic'
check blocked $'Fix hook\n\n'"$T1"': Claude Opus 5.5 <x@y>'
check blocked $'Fix hook\n\n'"$T1l"': claude <x@y>'
check blocked "Fix by bot <$T3.com>"
check blocked "🤖 $T2 [Claude Code](https://claude.com/claude-code)"
check blocked "$T2 Claude Code"
check clean   'Add CLAUDE.md and hook blocking public issue writes'
check clean   $'Fix hook\n\n'"$T1"': Sergio <s@example.com>'
check clean   'Docs: how Claude Code hooks work'
check clean   ''
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
