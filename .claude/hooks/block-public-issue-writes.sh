#!/usr/bin/env bash
set -uo pipefail

cmd=$(jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0
[ -n "$cmd" ] || exit 0

reason=$(printf '%s' "$cmd" | perl -e '
use strict; use warnings;
my $T = "sacon217/home-lab-ops";
my $WRITES = qr/create|new|edit|comment|close|reopen|delete|transfer|pin|unpin|lock|unlock|develop/;
my $GH = qr/(?:^|[\s(])(?:\S*\/)?gh\s+/;
my $SHELL = qr/\b(?:ba|z|da|k)?sh\b/;

my $ask;
local $/; my $raw = <STDIN>;
$raw =~ s/\\\n/ /g;

my @queue = ([$raw, 0]);
while (my $item = shift @queue) {
  my ($text, $depth) = @$item;
  next if $depth > 4;
  my @nested;

  $text =~ s{([^\n]*)<<-?[ \t]*(["\x27]?)(\w+)\2([^\n]*)\n(.*?)\n[ \t]*\3[ \t]*(?=\n|$)}{
    my ($pre, $delim, $post, $body) = ($1, $3, $4, $5);
    push @nested, $body if "$pre $post" =~ /$SHELL/ && $pre !~ /\$\(\s*cat\s*$/;
    "$pre<<$delim$post";
  }gse;

  if ($text =~ /${GH}api\s+graphql\b/i && ($text =~ /\bmutation\b/i || $text =~ /=\@|--input\b/)) {
    $ask //= "gh api graphql mutation (or a query read from a file): the target repo cannot be verified. Approve only if it does not write to the public repo.";
  }

  push @nested, $1 while $text =~ /\$\(([^()]*)\)/g;
  push @nested, $1 while $text =~ /`([^`]*)`/g;
  while ($text =~ /(?:$SHELL(?:\s+-\w+)*\s+-\w*c|\beval)\s+(["\x27])(.*?)(?<!\\)\1/gs) {
    my $body = $2;
    $ask //= "Command hidden in a variable (sh -c / eval): it cannot be checked. Approve only if it does not write issues to the public repo." if $body =~ /^\s*\$/;
    push @nested, $body;
  }
  for (@nested) { (my $n = $_) =~ s/\\(["\x27`\$])/$1/g; push @queue, [$n, $depth + 1]; }

  $text =~ s/(["\x27])((?:github\.com\/)?sacon217\/home-lab-ops)\1/$2/gi;
  $text =~ s/(["\x27])([^\s"\x27\\\$`;&|<>()\-][^\s"\x27\\\$`;&|<>()]*)\1/$2/g;
  $text =~ s{(["\x27])((?:https?://[^\s"\x27/]+)?/?repos/[^\s"\x27]+)\1}{$2}gi;
  $text =~ s/"(?:[^"\\]|\\.)*"/Q/gs;
  $text =~ s/\x27[^\x27]*\x27/Q/gs;
  $text =~ s/\\([A-Za-z])/$1/g;

  for my $seg (split /&&|\|\||;|\||\n/, $text) {
    $ask //= "gh subcommand is quoted or in a variable: it cannot be checked. Approve only if it does not write issues to the public repo." if $seg =~ /${GH}(?:issue\s+)?Q(?:\s|$)/
      || $seg =~ /^\s*(?:\w+=\S*\s+)*(?:Q|\$\{?\w+\}?|\$\([^)]*\))\s+(?:issue|api)\b/;
    if ($seg =~ /${GH}issue((?:\s+(?:-R|--repo)(?:=|\s+)\S+|\s+-\S+)*)\s+(?:$WRITES)(?:\s|$)/) {
      my @repos = $seg =~ /(?:^|\s)(?:-R|--repo)(?:=|\s*)(\S+)/g;
      my $repo = @repos ? $repos[-1] : "";
      (my $norm = lc $repo) =~ s{^github\.com/}{};
      if ($norm ne $T) {
        print "deny\tBlocked: gh issue write must target the private tracker with -R Sacon217/home-lab-ops (got \x27" . ($repo || "none") . "\x27). Write the repo name literally. This repo is public; see CLAUDE.md.";
        exit;
      }
    }
    if ($seg =~ /${GH}api\b/i) {
      my $method = $seg =~ /(?:^|\s)(?:-X|--method)(?:=|\s*)([A-Za-z]+)/ ? uc $1 : "";
      my $fields = $seg =~ /(?:^|\s)(?:-[fF]|--field|--raw-field|--input)/;
      my $write  = ($method && $method ne "GET") || (!$method && $fields);
      if ($write && $seg =~ m{repos/([^/\s]+/[^/\s]+)/issues}i && lc($1) ne $T) {
        print "deny\tBlocked: gh api write against issues of \x27$1\x27. Only repos/Sacon217/home-lab-ops may be written. See CLAUDE.md.";
        exit;
      }
      if ($write && !$ask) {
        my ($seen, $skip, $ep) = (0, 0, "");
        for my $t (split /\s+/, $seg) {
          if (!$seen) { $seen = 1 if $t eq "api"; next; }
          if ($skip) { $skip = 0; next; }
          if ($t =~ /^(?:-X|--method|-f|-F|--field|--raw-field|-H|--header|--input|-q|--jq|-t|--template|--hostname|--cache|-p|--preview)$/) { $skip = 1; next; }
          next if $t =~ /^-/;
          $ep = $t; last;
        }
        $ask = "gh api write to an endpoint that cannot be read (quoted or in a variable). Approve only if it does not write issues to the public repo." if $ep eq "Q" || $ep =~ /^\$/;
      }
    }
  }
}
print "ask\t$ask" if $ask;
')

if [ -n "$reason" ]; then
  jq -n --arg d "${reason%%$'\t'*}" --arg r "${reason#*$'\t'}" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: $d,
      permissionDecisionReason: $r
    }
  }'
fi
exit 0
