# Manual scoring-classifier test scenarios

This directory contains dummy files for manually testing the scoring-based
commit type classifier introduced for issues #72 and #74 and merged in PR #79.

There are at least five scenario files for each supported commit type:

- `feat`
- `fix`
- `docs`
- `style`
- `refactor`
- `test`
- `chore`
- `build`
- `ci`
- `perf`
- `revert`

## How to run a manual check

If you are on this branch after the files have been committed, first turn the
branch diff back into working-tree changes in a disposable checkout:

```bash
git reset --mixed origin/dev
```

Then, from the repository root:

```bash
./test-scenarios/bin/stage-expected.sh feat
git-acp --dry-run
```

Inspect the dry-run output and confirm the selected/generated commit type is
`feat`. Repeat with each expected value. The helper uses `git add -f` because
this repository's root `.gitignore` ignores untracked files by default.

## Suggested full loop

```bash
for expected in feat fix docs style refactor test chore build ci perf revert; do
  echo "=== Expected: ${expected} ==="
  ./test-scenarios/bin/stage-expected.sh "${expected}"
  git-acp --dry-run
  echo
done
git reset --quiet
```

## Scenario notes

### Production semantic types

`feat`, `fix`, `refactor`, and `perf` use production-style paths plus content
containing semantic evidence. These scenarios test that diff keywords can break
the production-file tie between feature, fix, refactor, and performance changes.

### Single-purpose path types

`docs`, `test`, `ci`, `build`, `style`, and `chore` are staged as category-only
changes. These scenarios test the classifier's single-purpose fast path and
file-category detection.

### Revert

`revert` is message-prefix driven in the current classifier. Files alone are
not expected to produce `revert`. To test revert classification, stage the
revert scenario and use a conventional commit message prefix, for example:

```bash
./test-scenarios/bin/stage-expected.sh revert
git-acp --dry-run --type revert
```

or run the normal flow and provide a message beginning with `revert:` if the
CLI prompts for one.

### Mixed commits

To test mixed-change behavior, stage files from multiple scenario directories,
for example:

```bash
git reset --quiet
git add test-scenarios/feat/src/features/user_profiles.py
git add test-scenarios/docs/docs/api-reference.md
git add test-scenarios/build/Dockerfile
git-acp --dry-run
```

The expected primary type should follow the strongest semantic signal, while
debug output may indicate mixed changes depending on the selected files.
