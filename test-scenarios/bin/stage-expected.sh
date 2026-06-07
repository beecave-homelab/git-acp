#!/usr/bin/env bash
set -euo pipefail

expected="${1:-}"
map_file="test-scenarios/expected-map.tsv"

usage() {
  cat <<'EOF'
Stage manual classifier samples for one expected outcome.

Usage:
  ./test-scenarios/bin/stage-expected.sh <expected>

Expected values:
  feat fix docs style refactor test chore build ci perf revert

The script resets the index, then stages only scenario files for the selected
outcome. It does not stage the manifest, README, or helper scripts.
EOF
}

if [[ -z "$expected" || "$expected" == "-h" || "$expected" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -f "$map_file" ]]; then
  echo "Error: manifest not found: $map_file" >&2
  exit 1
fi

matches="$(awk -F '	' -v expected="$expected" 'NR > 1 && $1 == expected { print $2 }' "$map_file")"
if [[ -z "$matches" ]]; then
  echo "Error: no sample files found for expected outcome: $expected" >&2
  exit 1
fi

git reset --quiet
while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  git add -f "$path"
done <<< "$matches"

echo "Staged files for expected outcome: $expected"
git diff --cached --name-only
