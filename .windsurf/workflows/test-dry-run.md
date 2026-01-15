---
description: Test dry-run mode with -a flag to verify working tree changes are detected
auto_execution_mode: 1
---

# Test Dry-Run Mode

Verify that `--dry-run` with `-a` correctly detects working tree changes without requiring actual staging.

## Prerequisites

Ensure you have unstaged changes in the working tree:

```bash
git status --porcelain=v1
git diff --name-only
```

These should include `test_dir1/` and `test_dir2/` directories with 2 files each. If not available ask the user to uncomment the lines in `.gitignore` to include these directories.

## Test Commands

### 1. Basic dry-run with all files

```bash
pdm run git-acp --dry-run --no-confirm -a "test_dir1/ test_dir2/" -mb "test message"
```

**Expected:** Should list files, show commit type analysis, and display "DRY RUN MODE" message. Should NOT show "No Changes Staged via -a".

### 2. Dry-run with AI message generation

```bash
pdm run git-acp -o --dry-run --no-confirm -a "test_dir1/ test_dir2/"
```

**Expected:** Should generate AI commit message and show dry-run preview.

### 3. Dry-run with specific directory scope

```bash
pdm run git-acp -o --dry-run --no-confirm -a test_dir1/
```

**Expected:** Should only consider files under `test_dir1/` directory.

### 4. Dry-run with verbose output

```bash
pdm run git-acp -o --dry-run --no-confirm -a "test_dir1/ test_dir2/" -v
```

**Expected:** Should show debug output including:

- `Debug - Dry-run mode enabled`
- `Git add: Skipping staging operations`
- `Debug - Getting changed files` with `staged_only=False`

### 5. Dry-run with extension patterns (root-level)

```bash
pdm run git-acp --dry-run --no-confirm -a "*.py *.md" -mb "test message"
```

**Expected:** Should match root-level `.py`/`.md` files and include subdirectory matches per scope filtering.

### 6. Dry-run with nested extension patterns

```bash
pdm run git-acp --dry-run --no-confirm -a "test_dir1/**/*.py test_dir2/**/*.md" -mb "test message"
```

**Expected:** Should only consider `.py` files under `test_dir1/` and `.md` files under `test_dir2/`.

### 7. Dry-run with mixed explicit paths and patterns

```bash
pdm run git-acp --dry-run --no-confirm -a "test_dir1/ *.md test_dir2/**" -mb "test message"
```

**Expected:** Should include explicit directory scopes plus pattern matches without staging anything.

### 8. Verify no actual staging occurred

After any dry-run command:

```bash
git diff --cached --name-only
```

**Expected:** Should be empty (no files staged).

## Unit Test

Run the regression test:

```bash
pdm run pytest tests/cli/test_workflow.py::TestGitWorkflow::test_dry_run_uses_working_tree_not_staged_for_check -v
```

## Full Workflow Test Suite

```bash
pdm run pytest tests/cli/test_workflow.py -v
```

## Finishing up

Let the user know to comment out the `test_dir1/` and `test_dir2/` entries in `.gitignore` to exclude these directories from tracking again.
