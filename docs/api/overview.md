# `git_acp` Package Documentation

**Version**: `0.17.0`
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
│   ├── ai_utils.py
│   └── client.py
├── cli/
│   ├── __init__.py
│   └── cli.py
├── config/
│   ├── __init__.py
│   ├── constants.py
│   └── env_config.py
├── git/
│   ├── __init__.py
│   ├── classification.py
│   ├── core.py
│   ├── diff.py
│   ├── git_operations.py
│   ├── history.py
│   ├── management.py
│   ├── operations.py
│   └── staging.py
├── utils/
│   ├── __init__.py
│   ├── formatting.py
│   └── types.py
├── __init__.py
└── __main__.py
```

---

## Top-Level Module (`git_acp`)

**Location**: `git_acp/__init__.py`
This is the root of the package and defines the package’s version.

- **Attributes**:
  - `__version__`: The version of the `git_acp` package.

**Example**:

```python
import git_acp

print(git_acp.__version__)  # "0.17.0"
```

---

## AI Subpackage (`git_acp.ai`)

**Location**: `git_acp/ai/__init__.py`, `git_acp/ai/ai_utils.py`, `git_acp/ai/client.py`

This subpackage contains functionality for AI-powered commit message generation. It integrates with an AI backend (e.g., Ollama).

### `git_acp.ai.__init__.py`

Exposes high-level AI helpers.

- `generate_commit_message(config: GitConfig) -> str`
  Convenience import that references `ai_utils.generate_commit_message`.

### `git_acp.ai.ai_utils`

Core logic for building commit context and prompts.

- **Functions**:
  - `create_advanced_commit_message_prompt(context: Dict[str, Any], config: OptionalConfig = None) -> str`
  - `create_simple_commit_message_prompt(context: Dict[str, Any], config: OptionalConfig = None) -> str`
  - `get_commit_context(config: GitConfig) -> Dict[str, Any]`
  - `edit_commit_message(message: str, config: GitConfig) -> str`
  - `generate_commit_message(config: GitConfig) -> str`

### `git_acp.ai.client`

Defines the `AIClient` class used to communicate with the AI model.

- **Class**: `AIClient`
  - `__init__(config: OptionalConfig = None)`
  - `chat_completion(messages: list[dict[str, str]], **kwargs) -> str`

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

Exports commonly used config objects and methods:

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
- `DEFAULT_FALLBACK_BASE_URL`
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

**Location**: `git_acp/git/`

Implements direct interaction with Git repositories (add, commit, push, diffs, history, branch management) and commit type classification. The subpackage is organized into several modules:

- `core.py` – defines `GitError` and `run_git_command`.
- `staging.py` – staging and pushing helpers: `get_current_branch`, `git_add`, `git_commit`, `git_push`, `unstage_files`, `setup_signal_handlers`.
- `diff.py` – file change detection and diff retrieval: `get_changed_files`, `get_diff`.
- `history.py` – commit history utilities: `get_recent_commits`, `find_related_commits`, `analyze_commit_patterns`.
- `management.py` – branch, remote, tag, and stash management: `create_branch`, `delete_branch`, `merge_branch`, `manage_remote`, `manage_tags`, `manage_stash`.
- `operations.py` – convenience layer re-exporting the above functions.
- `classification.py` – commit type helpers: `CommitType`, `classify_commit_type`, `get_changes`.
- `git_operations.py` – backward compatibility shim that re-exports from `operations`.

### `git_acp.git.__init__.py`

Re-exports commonly used operations:

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

### `git_acp.git.classification`

- **Enum**: `CommitType(Enum)` – conventional commit types with emojis. Includes `from_str(type_str: str) -> CommitType`.
- **Functions**:
  - `classify_commit_type(config) -> CommitType`
  - `get_changes() -> str`

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
    - `CommitDict = Dict[str, str]`
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
