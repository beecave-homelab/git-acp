# `git_acp` Package Documentation

**Version**: `0.14.2`  
**Summary**: The `git_acp` package is a command-line utility and Python API for automating common Git workflows with enhanced features such as:

- Interactive file selection
- AI-powered commit message generation
- Smart commit type classification
- Conventional commits support

Users can invoke these features via command-line interface (`git_acp.cli`), or programmatically through this package.

---

## Table of Contents

1. [Installation & Usage](#installation--usage)
2. [Package Layout](#package-layout)
3. [Top-Level Module (`git_acp`)](#top-level-module-git_acp)
4. [AI Subpackage (`git_acp.ai`)](#ai-subpackage-git_acpai)
5. [CLI Subpackage (`git_acp.cli`)](#cli-subpackage-git_acpcli)
6. [Configuration Subpackage (`git_acp.config`)](#configuration-subpackage-git_acpconfig)
7. [Git Subpackage (`git_acp.git`)](#git-subpackage-git_acpgit)
8. [Utilities Subpackage (`git_acp.utils`)](#utilities-subpackage-git_acputils)
9. [Command-Line Entry Point (`git_acp.__main__`)](#command-line-entry-point-git_acp__main__)

---

## Installation & Usage

You can install the `git_acp` package by cloning the repository or adding it to your Python environment. Once installed, you can:

- Use the CLI directly in a terminal:

  ```bash
  git-acp --help
  ```

- Or import it in your Python scripts to programmatically automate Git operations.

---

## Package Layout

```markdown
git_acp/
├── ai/
│   ├── __init__.py
│   └── ai_utils.py
├── cli/
│   ├── __init__.py
│   └── cli.py
├── config/
│   ├── __init__.py
│   ├── constants.py
│   └── env_config.py
├── git/
│   ├── __init__.py
│   ├── git_operations.py
│   └── classification.py
├── utils/
│   ├── __init__.py
│   ├── formatting.py
│   └── types.py
├── __init__.py
├── __main__.py
```

---

## Top-Level Module (`git_acp`)

**Location**: `git_acp/__init__.py`  
This is the root of the package. It defines the package's version and imports public-facing objects from submodules.

- **Attributes**:
  - `__version__`: The version of the `git_acp` package.

**Example**:

```python
import git_acp

print(git_acp.__version__)  # "0.14.0"
```

---

## AI Subpackage (`git_acp.ai`)

**Location**: `git_acp/ai/__init__.py` and `git_acp/ai/ai_utils.py`  

This subpackage contains functionality for AI-powered commit message generation. It integrates with an AI backend (e.g., Ollama).

### `git_acp.ai.__init__.py`

Exports public functions/classes from the AI subpackage.

- `generate_commit_message(config: GitConfig) -> str`  
  A convenience import that references `ai_utils.generate_commit_message`.

### `git_acp.ai.ai_utils`

Contains the core logic for generating commit messages with AI.

- **Function**: `generate_commit_message(config: GitConfig) -> str`  
  Generates a commit message using AI.  
  **Args**:  
  - `config (GitConfig)`: The user's Git configuration containing flags such as `use_ollama`, `verbose`, etc.  
  **Returns**:  
  - `str`: The AI-generated (and possibly user-edited) commit message.

- **Class**: `AIClient`  
  A client for interacting with the AI model.  
  **Methods**:
  1. `__init__(self, config: OptionalConfig = None)`: Initializes the AI client with default or custom base URLs, API keys, etc.
  2. `chat_completion(self, messages: list, **kwargs) -> str`: Sends a chat-style request to the AI model and returns the response text.

- **Function**: `create_advanced_commit_message_prompt(context: Dict[str, Any], config: OptionalConfig = None) -> str`  
  Creates a multi-context prompt for the AI to generate a more descriptive commit message.

- **Function**: `create_simple_commit_message_prompt(context: Dict[str, Any], config: OptionalConfig = None) -> str`  
  Creates a straightforward prompt for simpler commit messages.

- **Function**: `edit_commit_message(message: str, config: GitConfig) -> str`  
  Offers an interactive editing step for AI-generated commit messages if `interactive=True`.

- **Function**: `get_commit_context(config: GitConfig) -> Dict[str, Any]`  
  Gathers context from recent commits, staged diff, etc., to feed into AI prompts.

---

## CLI Subpackage (`git_acp.cli`)

**Location**: `git_acp/cli/__init__.py` and `git_acp/cli/cli.py`  

This subpackage provides the command-line interface using [Click](https://palletsprojects.com/p/click/).

### `git_acp.cli.__init__.py`

Exports the main CLI entry function:

- `main()`: The primary CLI entry function (imported from `cli.py`).

### `git_acp.cli.cli.py`

Implements the `main` command via Click decorators and subcommands/options.

- **Command**: `main`  
  **Usage**:

  ```bash
  git-acp [OPTIONS]
  ```

  **Options**:
  1. `-a, --add <file>`  
     Specify which files to stage. If not provided, an interactive file selection is displayed.
  2. `-m, --message <message>`  
     Specify a commit message directly.
  3. `-b, --branch <branch>`  
     Specify a branch to push to. Defaults to current branch if not provided.
  4. `-t, --type [feat|fix|docs|style|refactor|test|chore|revert]`  
     Manually specify commit type.
  5. `-o, --ollama`  
     Toggle AI-based commit message generation.
  6. `-i, --interactive`  
     If set, allows editing the AI-generated commit message.
  7. `-p, --prompt-type [simple|advanced]`  
     Choose AI prompt style. Defaults to `advanced`.
  8. `-nc, --no-confirm`  
     Skip confirmations.
  9. `-v, --verbose`  
     Print debug info.

**Primary Workflow**:

1. Gathers user input and config from CLI args.  
2. Selects files (or uses all if `-a` is not set).  
3. Optionally uses AI to generate commit message.  
4. Classifies or manually sets commit type.  
5. Commits and pushes to the specified or current branch.

---

## Configuration Subpackage (`git_acp.config`)

**Location**: `git_acp/config/__init__.py`, `git_acp/config/constants.py`, `git_acp/config/env_config.py`  

Manages environment variables, configuration constants, and user-defined settings.

### `git_acp.config.__init__.py`

Exports commonly used config objects and methods.

- **Exports**:
  - `COLORS`
  - `QUESTIONARY_STYLE`
  - `COMMIT_TYPES`
  - `COMMIT_TYPE_PATTERNS`
  - `EXCLUDED_PATTERNS`
  - `DEFAULT_REMOTE`
  - `DEFAULT_NUM_RECENT_COMMITS`
  - `DEFAULT_NUM_RELATED_COMMITS`
  - `DEFAULT_AI_MODEL`
  - `DEFAULT_TEMPERATURE`
  - `DEFAULT_BASE_URL`
  - `DEFAULT_API_KEY`
  - `DEFAULT_PROMPT_TYPE`
  - `DEFAULT_AI_TIMEOUT`
  - `TERMINAL_WIDTH`
  - `get_env`
  - `load_env_config`

### `git_acp.config.env_config`

- **Function**: `get_config_dir() -> Path`  
  Returns the path to `~/.config/git-acp`.
- **Function**: `ensure_config_dir() -> None`  
  Ensures that the `~/.config/git-acp` directory exists (creates if missing).
- **Function**: `load_env_config() -> None`  
  Loads environment variables from `.env` in the config directory if it exists.
- **Function**: `get_env(key: str, default: Any = None, type_cast: Optional[type] = None) -> Any`  
  Retrieves an environment variable, optionally casted to a specific type (e.g., `int`, `float`, `bool`).

### `git_acp.config.constants`

Defines constants for AI configuration, Git workflow configuration, file-exclusion patterns, commit type patterns, formatting colors, and terminal widths. These are loaded from environment variables where possible, otherwise defaulting to hardcoded fallback values.

---

## Git Subpackage (`git_acp.git`)

**Location**: `git_acp/git/__init__.py`, `git_acp/git/git_operations.py`, `git_acp/git/classification.py`  

Implements direct interaction with Git repositories (add, commit, push, logs, diffs, etc.) as well as commit type classification logic.

### `git_acp.git.__init__.py`

- **Exports**:
  - `GitError`
  - `run_git_command`
  - `get_current_branch`
  - `git_add`
  - `git_commit`
  - `git_push`
  - `get_changed_files`
  - `unstage_files`
  - `get_diff`
  - `get_recent_commits`
  - `find_related_commits`
  - `analyze_commit_patterns`
  - `CommitType`
  - `classify_commit_type`
  - `setup_signal_handlers`

### `git_acp.git.git_operations`

- **Class**: `GitError(Exception)`  
  Custom exception type for Git-related errors.

- **Function**: `run_git_command(command: list[str], config: OptionalConfig = None) -> Tuple[str, str]`  
  Runs a raw Git command using `subprocess.Popen` and returns `(stdout, stderr)` or raises `GitError`.

- **Function**: `get_current_branch(config: OptionalConfig = None) -> str`  
  Returns the currently checked-out Git branch name.

- **Function**: `git_add(files: str, config: OptionalConfig = None) -> None`  
  Stages specified files for commit. Accepts space-separated paths or `"."` for all.

- **Function**: `git_commit(message: str, config: OptionalConfig = None) -> None`  
  Commits staged changes with the provided commit message.

- **Function**: `git_push(branch: str, config: OptionalConfig = None) -> None`  
  Pushes the specified branch to the default remote (`origin`).

- **Function**: `get_changed_files(config: OptionalConfig = None) -> Set[str]`  
  Returns a set of changed file paths (staged or unstaged), filtering out excluded patterns.

- **Function**: `unstage_files(config: OptionalConfig = None) -> None`  
  Resets the staging area (equivalent to `git reset HEAD`).

- **Function**: `get_recent_commits(num_commits: int = DEFAULT_NUM_RECENT_COMMITS, config: OptionalConfig = None) -> List[Dict[str, str]]`  
  Fetches a specified number of recent commits in JSON-like form.

- **Function**: `find_related_commits(diff_content: str, num_commits: int = DEFAULT_NUM_RECENT_COMMITS, config: OptionalConfig = None) -> List[Dict[str, str]]`  
  Locates recently made commits that modified similar files/areas based on a diff.

- **Function**: `get_diff(diff_type: DiffType = "staged", config: OptionalConfig = None) -> str`  
  Retrieves the raw Git diff (staged or unstaged).

- **Function**: `create_branch(branch_name: str, config: OptionalConfig = None) -> None`  
  Creates and checks out a new branch.

- **Function**: `delete_branch(branch_name: str, force: bool = False, config: OptionalConfig = None) -> None`  
  Deletes a local branch. Use `force=True` to force-delete.

- **Function**: `merge_branch(source_branch: str, config: OptionalConfig = None) -> None`  
  Merges the specified source branch into the current branch.

- **Function**: `manage_remote(operation: Literal["add", "remove", "set-url"], remote_name: str, url: Optional[str] = None, config: OptionalConfig = None) -> None`  
  Adds, removes, or sets the URL of a Git remote.

- **Function**: `manage_tags(operation: Literal["create", "delete", "push"], tag_name: str, message: Optional[str] = None, config: OptionalConfig = None) -> None`  
  Creates, deletes, or pushes Git tags.

- **Function**: `manage_stash(operation: Literal["save", "pop", "apply", "drop", "list"], message: Optional[str] = None, stash_id: Optional[str] = None, config: OptionalConfig = None) -> Optional[str]`  
  Performs stash operations, returning the stash list for `list` operation.

- **Function**: `analyze_commit_patterns(commits: List[Dict[str, str]], config: OptionalConfig = None) -> Dict[str, Dict[str, int]]`  
  Analyzes commit messages to find frequent types and scopes (e.g., `feat`, `fix`).

- **Function**: `setup_signal_handlers() -> None`  
  Installs signal handlers to gracefully unstage files and exit on `CTRL+C`.

### `git_acp.git.classification`

- **Enum**: `CommitType(Enum)`  
  Enumerates conventional commit types (FEAT, FIX, DOCS, etc.) with optional emojis.  
  **Method**:
  - `from_str(type_str: str) -> CommitType`: Converts a string to a `CommitType` or raises `GitError`.

- **Function**: `classify_commit_type(config) -> CommitType`  
  Examines the current diff and determines the most likely commit type based on patterns defined in `git_acp.config.constants.COMMIT_TYPE_PATTERNS`.

- **Function**: `get_changes() -> str`  
  Retrieves staged or unstaged changes as a diff string, throwing `GitError` if none exist.

---

## Utilities Subpackage (`git_acp.utils`)

**Location**: `git_acp/utils/__init__.py`, `git_acp/utils/formatting.py`, `git_acp/utils/types.py`

General-purpose helper functions, formatting, and type definitions used throughout the package.

### `git_acp.utils.__init__.py`

Re-exports commonly used utility functions and type definitions:

- `debug_header`
- `debug_item`
- `debug_json`
- `debug_preview`
- `status`
- `success`
- `warning`
- `GitConfig`
- `OptionalConfig`
- `DiffType`
- `PromptType`

### `git_acp.utils.formatting`

Provides functionality for printing styled debug and status messages using [Rich](https://github.com/Textualize/rich).

- **Function**: `debug_header(message: str) -> None`  
  Prints a debug header with special styling.

- **Function**: `debug_item(label: str, value: str = None) -> None`  
  Prints a label-value pair for debugging.

- **Function**: `debug_json(data: dict, indent: int = 4) -> None`  
  Prints JSON data in a styled format.

- **Function**: `debug_preview(text: str, num_lines: int = 10) -> None`  
  Prints the first `num_lines` of text.

- **Function**: `success(message: str) -> None`  
  Prints a success message with a checkmark.

- **Function**: `warning(message: str) -> None`  
  Prints a warning message.

- **Function**: `status(message: str) -> Console.status`  
  Creates a Rich console status context manager to show progress on long-running tasks.

### `git_acp.utils.types`

Defines custom data classes and type aliases used throughout `git_acp`.

- **Dataclass**: `GitConfig`  
  Holds settings for Git operations:

  ```python
  @dataclass
  class GitConfig:
      files: str = "."
      message: str = "Automated commit"
      branch: Optional['GitConfig'] = None
      use_ollama: bool = False
      interactive: bool = False
      skip_confirmation: bool = False
      verbose: bool = False
      prompt_type: str = "advanced"
  ```

- **Type Aliases**:
  - `OptionalConfig = Optional[GitConfig]`
  - `DiffType = Literal["staged", "unstaged"]`
  - `RemoteOperation = Literal["add", "remove", "set-url"]`
  - `TagOperation = Literal["create", "delete", "push"]`
  - `StashOperation = Literal["save", "pop", "apply", "drop", "list"]`
  - `PromptType = Literal["simple", "advanced"]`
  - `Message = Dict[str, str]`
  - `CommitContext = Dict[str, Any]`

---

## Command-Line Entry Point (`git_acp.__main__`)

**Location**: `git_acp/__main__.py`

Provides a Python entry point so you can run:

```bash
python -m git_acp
```

which simply invokes the CLI (`git_acp.cli.main`).

---

## Example Usage

Below is a simple command-line usage example:

```bash
# Stage and commit all files with an AI-generated message, skipping confirmation:
git-acp --ollama --no-confirm

# Or specify a custom commit message directly:
git-acp -a "." -m "Refactor module to improve performance" --type refactor
```

If you want to incorporate this in a Python script:

```python
from git_acp.config import get_env
from git_acp.git import git_add, git_commit, git_push, GitError

try:
    git_add(".")
    git_commit("Automated commit")
    git_push("main")
except GitError as e:
    print(f"Git error occurred: {e}")
```

---

**That concludes the API documentation for the `git_acp` package.**

Use it to automate git tasks with helpful interactive selection, AI-assisted commit messages, and standardized commit types.
