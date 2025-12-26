<!-- This is an auto-generated reply by CodeRabbit -->
# Coding Plan

## Approach

Add an optional `--auto-group` flag that automatically groups related file changes and creates multiple focused commits, each using the existing git-acp workflow (stage → AI message generation → commit → push).

## Observations

`git-acp` is a CLI tool built with Click that orchestrates git add/commit/push workflows with AI-generated commit messages. The architecture uses a modular, functional design with clear separation: CLI layer (argument parsing and main execution), workflow orchestration (`GitWorkflow` class), git operations (stateless functions for add/commit/push), AI integration (message generation), and configuration management (`constants` with pattern-based file classification). The existing `FILE_PATH_PATTERNS` system already classifies files by commit type (test, docs, chore, style) using path matching with a 50% threshold, making it a natural foundation for grouping logic.

## Assumptions

Assumption 1: Should auto-grouping create separate commits for each group or allow interactive selection per group?

**Options Considered:**

- Fully automatic mode that commits all groups without interaction
- Interactive mode that shows each group and asks for confirmation
- Hybrid mode that groups automatically but still allows file selection refinement per group

**Chosen Option:** Fully automatic mode that commits all groups without interaction

**Rationale:** When `--auto-group` is enabled, the tool will create commits for all detected groups without additional prompts beyond those controlled by existing flags like `--no-confirm`. This aligns with the ticket's goal of minimizing manual steps and cognitive overhead. Users can combine with `--no-confirm` for fully hands-off operation, or run without `--auto-group` if they want manual control. The grouping algorithm should be conservative (prefer smaller, more focused groups) to ensure commits remain logical and reviewable.

Assumption 2: How should the grouping algorithm handle files that don't match any classification patterns?

**Options Considered:**

- Create a single "mixed" commit for all unmatched files
- Group by directory structure (files in same directory go together)
- Group by file extension (all .py together, all .md together, etc.)
- Create individual commits for each unmatched file

**Chosen Option:** Group by directory structure with a fallback to file extension grouping

**Rationale:** This feels natural because files in the same directory often represent related functionality, and developers mentally organize code this way. If directory grouping produces too many tiny groups (e.g., one file per directory), fall back to extension-based grouping to avoid commit spam. This approach balances meaningful logical grouping with practical commit granularity.

## Implementation Steps

### Phase 1: Add CLI Flag and Configuration

Add the `--auto-group` flag to the CLI interface and pass the configuration through the existing parameter flow.

Task 1: Add CLI Flag Definition

Add the `--auto-group` flag using Click's decorator pattern in the main command definition.

- Add `@click.option("--auto-group", "-ag", is_flag=True, default=False, help="Automatically group related changes into multiple focused commits")` in `git_acp/cli/cli.py` alongside existing flags like `--ollama`
- Update the `main()` function signature to accept the new `auto_group` parameter
- Follow the same boolean flag pattern used by `--ollama`, `--dry-run`, etc.

Task 2: Pass Flag to Workflow

Extend the configuration flow to make the auto-group setting available throughout the workflow execution.

- Add `auto_group` field to the `GitConfig` class in `git_acp/utils/types.py` (or wherever GitConfig is defined)
- In `git_acp/cli/cli.py` main(), set `config.auto_group = auto_group` when building the config object
- This maintains the existing pattern of storing all execution parameters in the config object

🤖 Prompt for AI agents

```md
Add `--auto-group` CLI flag and wire it through the configuration system.

In git_acp/cli/cli.py:
- Add `@click.option("--auto-group", "-ag", is_flag=True, default=False,
help="Automatically group related changes into multiple focused commits")`
decorator
- Add `auto_group` parameter to main() function signature
- Set `config.auto_group = auto_group` when building the config object

In git_acp/utils/types.py:
- Add `auto_group` boolean field to GitConfig class
```

### Phase 2: Implement File Grouping Logic

Create a pure function that groups changed files based on existing classification patterns and directory structure with deterministic ordering.

Task 1: Create Grouping Function

Add a new function in the git module that analyzes changed files and produces logical groups with stable ordering.

- Create `group_changed_files(files: set[str]) -> list[list[str]]` in `git_acp/git/classification.py` (or create new `git_acp/git/grouping.py`)
- Return a list of sorted file lists (changed from set to list for determinism), where each list represents files that should be committed together
- Ensure function is pure (no side effects) for easy testing

Task 2: Implement Classification-Based Grouping with Priority Ordering

Use existing FILE_PATH_PATTERNS to perform the primary grouping with a fixed commit-type priority.

- Define fixed priority order for commit types: `["docs", "test", "style", "chore"]` (most to least likely to be standalone)
- For each file in the input set, determine which commit type it matches using the existing `_match_file_path_pattern()` helper
- Create separate groups for each matched commit type, maintaining the priority order
- Store unmatched files separately for secondary grouping
- Within each commit-type group, sort files alphabetically for deterministic output

Task 3: Implement Fallback Grouping with Deterministic Ordering

Handle files that don't match any classification pattern using directory structure and file extensions with stable sorting.

- Extract common directory prefixes from unmatched files (e.g., "src/api/", "src/models/") and sort the prefixes alphabetically
- Group files that share the same directory prefix (up to 2-3 levels deep), sorted by directory prefix
- If a directory contains only 1-2 files, group by file extension instead
- Sort extension-based groups by extension name alphabetically
- Within each directory or extension group, sort files alphabetically
- Apply EXCLUDED_PATTERNS filtering to ensure no excluded files end up in groups
- Return groups in order: commit-type groups (in priority order) followed by directory groups (sorted) followed by extension groups (sorted)

🤖 Prompt for AI agents

```md
Implement the `group_changed_files()` function with deterministic grouping
logic.

Create pure function in git_acp/git/classification.py (or new grouping.py):
- Function signature: `group_changed_files(files: set[str]) -> list[list[str]]`
- Define commit-type priority order: ["docs", "test", "style", "chore"]
- Use existing `_match_file_path_pattern()` to classify files
- Group files by commit type first, maintaining priority order
- For unmatched files: group by common directory prefix (2-3 levels deep)
- If directory groups are too small (1-2 files), fall back to extension-based
grouping
- Sort files alphabetically within each group
- Sort groups by priority (commit-types first, then directories, then
extensions)
- Filter using EXCLUDED_PATTERNS
- Return list of sorted file lists
```

### Phase 3: Modify Main Execution Flow

Update the CLI main function to detect the auto-group flag and orchestrate multiple workflow executions with proper validation and user feedback.

Task 1: Add Staged Files Validation

Implement the staged files policy before any grouping occurs.

- In `git_acp/cli/cli.py` main(), immediately after checking `if config.auto_group:`, call `get_changed_files(config, staged_only=True)`
- If the result is non-empty, print error message: "Cannot use --auto-group with files already staged. Please commit, stash, or unstage existing changes first."
- Exit with return code 1
- This prevents mixing manually-staged files with auto-grouped commits

Task 2: Add Conditional Branching in Main

Modify the main() function to branch between single-commit and multi-commit execution paths.

- In `git_acp/cli/cli.py` main(), after staged files validation, check `if config.auto_group:`
- For single-commit mode (existing): instantiate GitWorkflow and call run() once (no changes to existing flow)
- For auto-group mode (new): proceed to grouping and multi-commit loop

Task 3: Implement Multi-Commit Loop with Per-Group Config

Create the execution loop that processes each file group through the existing workflow using independent config objects.

- Call `get_changed_files(config, staged_only=False)` to get all unstaged files
- If no changed files exist, print message and exit early (follow existing pattern)
- Call `group_changed_files(changed_files)` to get the ordered list of file groups
- Print pre-run summary: "Auto-grouping detected {len(groups)} groups. This will create {len(groups)} commits and make {len(groups)} AI requests."
- For each group in the list:
  - Create a new config object: `group_config = copy.copy(config)` or use a factory function
  - Set `group_config.files = group` (the sorted file list)
  - Instantiate a new `GitWorkflow` instance with `files_from_cli=True` to signal pre-selected files
  - Call `workflow.run()`
  - If run() returns non-zero, print warning but continue to next group (graceful degradation)
  - Call `unstage_files()` before processing next group to ensure clean state
- Print summary at end showing number of commits created

Task 4: Handle Edge Cases and User Feedback

Add appropriate messages and error handling for the multi-commit flow.

- Before starting loop, print informative message: "Starting auto-group workflow with {len(groups)} groups..."
- After each successful commit, print brief status: "✓ Committed group {n} of {total}: [{', '.join(group[:3])}{'...' if len(group) > 3 else ''}]"
- If any group fails, log the failure: "✗ Group {n} failed: {error_message}" but continue processing remaining groups
- At the end, print final summary: "Auto-group complete: {success_count} commits created, {failure_count} groups failed"
- Ensure EXCLUDED_PATTERNS are respected by relying on `get_changed_files()` filtering (already implemented)

🤖 Prompt for AI agents

```md
Implement multi-commit orchestration in the CLI main() function.

In git_acp/cli/cli.py main():
- Check for staged files when `config.auto_group` is True
- If staged files exist, print error and exit with code 1
- Add conditional branch: if auto_group, enter multi-commit mode; else use
existing single-commit flow
- In multi-commit mode:
  - Get all unstaged files via `get_changed_files(config, staged_only=False)`
  - Call `group_changed_files()` to get file groups
  - Print pre-run summary showing group count
  - Loop through each group:
    - Create per-group config copy with `group_config.files = group`
    - Instantiate GitWorkflow with `files_from_cli=True`
    - Call workflow.run()
    - Handle errors gracefully and continue
    - Call `unstage_files()` after each iteration
  - Print status messages per group and final summary
```

### Phase 4: Ensure Workflow Compatibility

Verify and adjust GitWorkflow to ensure it can be safely called multiple times with proper staging hygiene between iterations.

Task 1: Review GitWorkflow State Management

Ensure GitWorkflow doesn't maintain state that would break on repeated executions.

- Review instance variables in `git_acp/cli/workflow.py` GitWorkflow class
- Verify that `config`, `interaction`, `_files_from_cli`, `_commit_type_override` are safe for multiple instantiations
- Confirm that mutating `config.message`, `config.branch` in one instance doesn't affect subsequent instances when using per-group configs

Task 2: Define Staging Invariants Between Groups

Establish and enforce the staging state contract before and after each group.

- **Before-group invariant:** Staging area must be empty before processing each group
- **After-group invariant:** For successful commits, staging area is automatically cleared by git commit; for failed commits, staging area must be cleaned via `unstage_files()`
- Implement explicit `unstage_files()` call in Phase 3 Task 3.3 loop after each workflow.run() to guarantee invariant
- Add defensive check: before staging files for a new group, verify staging area is clean by calling `get_changed_files(config, staged_only=True)` and raising error if non-empty (should never happen if invariants are maintained)

Task 3: Adjust Workflow for Multi-Group Context

Make minor adjustments to GitWorkflow behavior when running in auto-group mode.

- When `files_from_cli=True` is set during GitWorkflow instantiation, skip the interactive file selection prompt (files are pre-selected by grouping)
- Ensure the workflow respects the pre-selected files in `config.files` and doesn't prompt user to modify the selection
- Maintain all other workflow behaviors (AI generation, commit type classification, confirmations controlled by existing flags) unchanged
- Verify that `--dry-run` flag correctly stops execution before commit for each group iteration

Task 4: Handle Cleanup and Error Recovery

Ensure proper cleanup between workflow iterations to prevent partial state leakage.

- In Phase 3 Task 3.3 loop, wrap individual workflow.run() calls in try-except to catch exceptions
- On exception or non-zero return: call `unstage_files(config)` to ensure clean state, log error, and continue to next group
- If push fails for one group, log the error and continue with remaining groups (commits are still safe locally)
- Track successful commits vs. failed groups for the final summary message
- Maintain the same error handling patterns used in the single-commit flow

🤖 Prompt for AI agents

```md
Ensure GitWorkflow can be safely called multiple times with proper state
management.

In git_acp/cli/workflow.py:
- Review GitWorkflow instance variables for state isolation
- When `files_from_cli=True`, skip interactive file selection prompt
- Respect pre-selected files in `config.files`
- Verify `--dry-run` flag works correctly in multi-group context

In git_acp/cli/cli.py multi-commit loop:
- Wrap workflow.run() in try-except for error handling
- Call `unstage_files()` after each iteration (success or failure)
- Add defensive check before staging: verify staging area is empty
- Track success/failure counts for final summary
- Continue processing remaining groups on individual failures
```

### Phase 5: Export and Document New Functionality

Make the grouping function available through the public API and add basic in-code documentation.

Task 1: Update Module Exports

Add the new grouping function to the appropriate module's public interface.

- In `git_acp/git/__init__.py`, import and re-export `group_changed_files` from classification.py or grouping.py
- Follow the existing export pattern used for `git_add`, `git_commit`, `git_push`, etc.
- Update `__all__` list to include the new function

Task 2: Add Function Documentation

Document the grouping function's behavior and heuristics.

- Add comprehensive docstring to `group_changed_files()` explaining:
  - Grouping algorithm (priority-based classification, directory fallback, extension fallback)
  - Deterministic ordering guarantees (commit-type priority, alphabetical sorting)
  - Input/output format (set of file paths → list of sorted file lists)
  - Example showing how files would be grouped
- Document that the function uses FILE_PATH_PATTERNS for primary classification
- Explain the fallback behavior for unmatched files (directory structure → file extension)
- Note that EXCLUDED_PATTERNS filtering is assumed to happen in `get_changed_files()` before calling this function

🤖 Prompt for AI agents

```md
Export and document the grouping function.

In git_acp/git/__init__.py:
- Import `group_changed_files` from classification.py or grouping.py
- Add to `__all__` list
- Follow existing export patterns

In the grouping function:
- Add comprehensive docstring covering:
- Algorithm description (commit-type priority, directory fallback, extension
fallback)
  - Deterministic ordering guarantees
  - Input/output format with types
  - Usage example
  - Notes on FILE_PATH_PATTERNS and EXCLUDED_PATTERNS
```

### Phase 6: Testing

Add comprehensive test coverage for the grouping logic and multi-commit orchestration.

Task 1: Unit Tests for Grouping Function

Create tests in `tests/git/test_grouping.py` (or extend `tests/git/test_classification.py`) to verify grouping behavior.

- Test commit-type classification: files matching FILE_PATH_PATTERNS are grouped correctly
- Test priority ordering: commit-type groups appear in the correct order (docs, test, style, chore)
- Test deterministic file ordering: files within groups are sorted alphabetically
- Test directory fallback: unmatched files are grouped by common directory prefix
- Test extension fallback: files with no common directory are grouped by extension
- Test deterministic group ordering: directory and extension groups are sorted
- Test EXCLUDED_PATTERNS: verify excluded files don't appear in any groups (if passed to function)
- Test edge cases: empty input, single file, all files match one pattern, no files match any pattern

Task 2: Integration Tests for Multi-Commit Workflow

Create tests in `tests/cli/test_auto_group.py` to verify the end-to-end behavior.

- Test that `--auto-group` triggers multiple workflow.run() calls (mock GitWorkflow)
- Test staged files validation: should exit with error when staging area is non-empty
- Test staging cleanup: verify `unstage_files()` is called between groups
- Test failure handling: verify that one group failure doesn't stop subsequent groups
- Test per-group config isolation: verify mutating one group's config doesn't affect others
- Test flag interactions: verify `--auto-group --no-confirm` skips prompts, `--auto-group --dry-run` exits before commit
- Test summary output: verify group count and success/failure messages are printed

Task 3: Run Standard Checks

Execute the repository's standard testing and linting commands.

- Run `pdm run ruff check --fix .` to check and auto-fix linting issues
- Run `pdm run ruff format .` to ensure code formatting is consistent
- Run `pdm run pytest -q` to execute all tests and verify they pass
- Verify test naming follows repository convention: `test_<unit>__<expected_behavior>()`
- Add tests to appropriate directories following the existing structure: `tests/git/`, `tests/cli/`

🤖 Prompt for AI agents

```md
Add comprehensive test coverage for auto-grouping functionality.

Create tests/git/test_grouping.py (or extend test_classification.py):
- Test commit-type classification and priority ordering
- Test deterministic file and group ordering
- Test directory and extension fallback logic
- Test EXCLUDED_PATTERNS filtering
- Test edge cases (empty input, single file, etc.)

Create tests/cli/test_auto_group.py:
- Mock GitWorkflow and test multiple run() calls
- Test staged files validation error
- Test staging cleanup between groups
- Test error handling and graceful degradation
- Test per-group config isolation
- Test flag interactions (--no-confirm, --dry-run)
- Test summary output messages

Run standard checks:
- `pdm run ruff check --fix .`
- `pdm run ruff format .`
- `pdm run pytest -q`
```

---

### 🚀 Next Steps

🤖 All AI agent prompts combined

```md
Task: 1

Add `--auto-group` CLI flag and wire it through the configuration system.

In git_acp/cli/cli.py:
- Add `@click.option("--auto-group", "-ag", is_flag=True, default=False,
help="Automatically group related changes into multiple focused commits")`
decorator
- Add `auto_group` parameter to main() function signature
- Set `config.auto_group = auto_group` when building the config object

In git_acp/utils/types.py:
- Add `auto_group` boolean field to GitConfig class
===============================================================================

Task: 2

Implement the `group_changed_files()` function with deterministic grouping
logic.

Create pure function in git_acp/git/classification.py (or new grouping.py):
- Function signature: `group_changed_files(files: set[str]) -> list[list[str]]`
- Define commit-type priority order: ["docs", "test", "style", "chore"]
- Use existing `_match_file_path_pattern()` to classify files
- Group files by commit type first, maintaining priority order
- For unmatched files: group by common directory prefix (2-3 levels deep)
- If directory groups are too small (1-2 files), fall back to extension-based
grouping
- Sort files alphabetically within each group
- Sort groups by priority (commit-types first, then directories, then
extensions)
- Filter using EXCLUDED_PATTERNS
- Return list of sorted file lists
===============================================================================

Task: 3

Implement multi-commit orchestration in the CLI main() function.

In git_acp/cli/cli.py main():
- Check for staged files when `config.auto_group` is True
- If staged files exist, print error and exit with code 1
- Add conditional branch: if auto_group, enter multi-commit mode; else use
existing single-commit flow
- In multi-commit mode:
  - Get all unstaged files via `get_changed_files(config, staged_only=False)`
  - Call `group_changed_files()` to get file groups
  - Print pre-run summary showing group count
  - Loop through each group:
    - Create per-group config copy with `group_config.files = group`
    - Instantiate GitWorkflow with `files_from_cli=True`
    - Call workflow.run()
    - Handle errors gracefully and continue
    - Call `unstage_files()` after each iteration
  - Print status messages per group and final summary
===============================================================================

Task: 4

Ensure GitWorkflow can be safely called multiple times with proper state
management.

In git_acp/cli/workflow.py:
- Review GitWorkflow instance variables for state isolation
- When `files_from_cli=True`, skip interactive file selection prompt
- Respect pre-selected files in `config.files`
- Verify `--dry-run` flag works correctly in multi-group context

In git_acp/cli/cli.py multi-commit loop:
- Wrap workflow.run() in try-except for error handling
- Call `unstage_files()` after each iteration (success or failure)
- Add defensive check before staging: verify staging area is empty
- Track success/failure counts for final summary
- Continue processing remaining groups on individual failures
===============================================================================

Task: 5

Export and document the grouping function.

In git_acp/git/__init__.py:
- Import `group_changed_files` from classification.py or grouping.py
- Add to `__all__` list
- Follow existing export patterns

In the grouping function:
- Add comprehensive docstring covering:
- Algorithm description (commit-type priority, directory fallback, extension
fallback)
  - Deterministic ordering guarantees
  - Input/output format with types
  - Usage example
  - Notes on FILE_PATH_PATTERNS and EXCLUDED_PATTERNS
===============================================================================

Task: 6

Add comprehensive test coverage for auto-grouping functionality.

Create tests/git/test_grouping.py (or extend test_classification.py):
- Test commit-type classification and priority ordering
- Test deterministic file and group ordering
- Test directory and extension fallback logic
- Test EXCLUDED_PATTERNS filtering
- Test edge cases (empty input, single file, etc.)

Create tests/cli/test_auto_group.py:
- Mock GitWorkflow and test multiple run() calls
- Test staged files validation error
- Test staging cleanup between groups
- Test error handling and graceful degradation
- Test per-group config isolation
- Test flag interactions (--no-confirm, --dry-run)
- Test summary output messages

Run standard checks:
- `pdm run ruff check --fix .`
- `pdm run ruff format .`
- `pdm run pytest -q`
```

💡 Iterate on the plan with: `@coderabbitai <feedback>`

```md
Example Feedback
- @coderabbitai You can skip phase 3. Add a simple unit test case for phase 2.
- @coderabbitai For assumption 1 go ahead with option 3 and replan.
```

---

💬 Have feedback or questions? Drop into our [discord](https://discord.gg/coderabbit)!
