#!/usr/bin/env bash
# PreToolUse hook (Bash): issue writes may only target the private tracker Sacon217/home-lab-ops.
# This repo is public; a security finding filed here is free recon for anyone.
# Best-effort guard against an agent's mistake, not a sandbox: it fails closed on what it can parse.
# Tests: bash .claude/hooks/test-block-public-issue-writes.sh
set -uo pipefail

cmd=$(jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0
[ -n "$cmd" ] || exit 0

reason=$(printf '%s' "$cmd" | perl -e '
use strict; use warnings;
my $T = "sacon217/home-lab-ops";
my $WRITES = qr/create|new|edit|comment|close|reopen|delete|transfer|pin|unpin|lock|unlock|develop/;
my $GH = qr/(?:^|[\s(])(?:\S*\/)?gh\s+/;
my $SHELL = qr/\b(?:ba|z|da|k)?sh\b/;

local $/; my $raw = <STDIN>;
$raw =~ s/\\\n/ /g;    # join line continuations

my @queue = ([$raw, 0]);
while (my $item = shift @queue) {
  my ($text, $depth) = @$item;
  next if $depth > 4;
  my @nested;

  # Heredoc bodies are data, unless fed to a shell: then they are commands.
  $text =~ s{([^\n]*)<<-?[ \t]*(["\x27]?)(\w+)\2([^\n]*)\n(.*?)\n[ \t]*\3[ \t]*(?=\n|$)}{
    my ($pre, $delim, $post, $body) = ($1, $3, $4, $5);
    push @nested, $body if "$pre $post" =~ /$SHELL/ && $pre !~ /\$\(\s*cat\s*$/;
    "$pre<<$delim$post";
  }gse;

  # GraphQL mutations: we cannot tell which repo they hit, so issue/comment mutations are denied.
  if ($text =~ /${GH}api\s+graphql\b/i && $text =~ /\bmutation\b/i && $text =~ /issue|comment/i) {
    print "Blocked: gh api graphql issue/comment mutations are not allowed here. Use REST against repos/Sacon217/home-lab-ops."; exit;
  }

  # Commands nested in $(...), backticks, sh -c "...", eval "..." get checked on their own.
  push @nested, $1 while $text =~ /\$\(([^()]*)\)/g;
  push @nested, $1 while $text =~ /`([^`]*)`/g;
  push @nested, $2 while $text =~ /(?:$SHELL(?:\s+-\w+)*\s+-\w*c|\beval)\s+(["\x27])(.*?)(?<!\\)\1/gs;
  for (@nested) { (my $n = $_) =~ s/\\(["\x27`\$])/$1/g; push @queue, [$n, $depth + 1]; }

  # Top level: unquote the tracker name and a quoted "gh", blank all other quoted text.
  $text =~ s/(["\x27])((?:github\.com\/)?sacon217\/home-lab-ops)\1/$2/gi;
  $text =~ s/(["\x27])gh\1/gh/g;
  $text =~ s{(["\x27])((?:https?://[^\s"\x27/]+)?/?repos/[^\s"\x27]+)\1}{$2}gi;  # quoted API endpoints
  $text =~ s/"(?:[^"\\]|\\.)*"/Q/gs;
  $text =~ s/\x27[^\x27]*\x27/Q/gs;

  for my $seg (split /&&|\|\||;|\||\n/, $text) {
    # gh issue <write>, allowing flags between "issue" and the verb
    if ($seg =~ /${GH}issue((?:\s+(?:-R|--repo)(?:=|\s+)\S+|\s+-\S+)*)\s+(?:$WRITES)(?:\s|$)/) {
      my @repos = $seg =~ /(?:^|\s)(?:-R|--repo)(?:=|\s*)(\S+)/g;
      my $repo = @repos ? $repos[-1] : "";
      (my $norm = lc $repo) =~ s{^github\.com/}{};
      if ($norm ne $T) {
        print "Blocked: gh issue write must target the private tracker with -R Sacon217/home-lab-ops (got \x27" . ($repo || "none") . "\x27). Write the repo name literally. This repo is public; see CLAUDE.md.";
        exit;
      }
    }
    # gh api REST writes to any issues endpoint other than the tracker
    if ($seg =~ /${GH}api\b/i) {
      my $method = $seg =~ /(?:^|\s)(?:-X|--method)(?:=|\s*)([A-Za-z]+)/ ? uc $1 : "";
      my $fields = $seg =~ /(?:^|\s)(?:-[fF]|--field|--raw-field|--input)/;
      my $write  = ($method && $method ne "GET") || (!$method && $fields);
      if ($write && $seg =~ m{repos/([^/\s]+/[^/\s]+)/issues}i && lc($1) ne $T) {
        print "Blocked: gh api write against issues of \x27$1\x27. Only repos/Sacon217/home-lab-ops may be written. See CLAUDE.md.";
        exit;
      }
    }
  }
}
')

if [ -n "$reason" ]; then
  jq -n --arg r "$reason" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $r
    }
  }'
fi
exit 0
