# `git_acp` Package Documentation

**Version**: `0.15.0`  
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
│   ├── generation.py
│   ├── client.py
│   └── prompts.py
├── cli/
│   ├── __init__.py
│   ├── cli.py
│   ├── helpers.py
│   ├── prompts.py
│   └── formatting.py
├── config/
│   ├── __init__.py
│   ├── constants.py
│   ├── env_config.py
│   ├── loader.py
│   └── settings.py
├── git/
│   ├── __init__.py
│   ├── runner.py
│   ├── branch.py
│   ├── classification.py
│   ├── commit.py
│   ├── history.py
│   ├── remote.py
│   ├── stash.py
│   ├── status.py
│   └── tag.py
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

print(git_acp.__version__)  # "0.15.0"
```

---

## AI Subpackage (`git_acp.ai`)

**Location**: `git_acp/ai/__init__.py`, `git_acp/ai/generation.py`, `git_acp/ai/client.py`, and `git_acp/ai/prompts.py`

This subpackage contains functionality for AI-powered commit message generation. It integrates with an AI backend (e.g., Ollama).

### `git_acp.ai.__init__.py`

Exports public functions/classes from the AI subpackage.

- `generate_commit_message(config: GitConfig) -> str`  
  A convenience import that references `generation.py`.

### `git_acp.ai.generation.py`

Contains the core logic for generating commit messages with AI.

- **Function**: `generate_commit_message(config: GitConfig) -> str`  
  Generates a commit message using AI.  
  **Args**:  
  - `config (GitConfig)`: The user's Git configuration containing flags such as `use_ollama`, `verbose`, etc.  
  **Returns**:  
  - `str`: The AI-generated (and possibly user-edited) commit message.

### `git_acp.ai.client.py`

- **Class**: `AIClient`  
  A client for interacting with the AI model.  
  **Methods**:
  1. `__init__(self, config: OptionalConfig = None)`: Initializes the AI client with default or custom base URLs, API keys, etc.
  2. `chat_completion(self, messages: list, **kwargs) -> str`: Sends a chat-style request to the AI model and returns the response text.

### `git_acp.ai.prompts.py`

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

**Location**: `git_acp/cli/__init__.py`, `git_acp/cli/cli.py`, `git_acp/cli/helpers.py`, `git_acp/cli/prompts.py`, and `git_acp/cli/formatting.py`

This subpackage provides the command-line interface using Click decorators. It supports:

- **Entry Point**:  
  `main()` in `cli.py` which orchestrates file selection, commit message generation (including AI features), commit type classification, and executing Git commands.

- **Interactive Helpers**:  
  `helpers.py` and `prompts.py` provide interactive file selection and commit type prompts.

- **Formatting**:  
  `formatting.py` offers functions to format commit messages in a conventional style.

**Primary Workflow**:

1. Gathers user input and config from CLI args.  
2. Selects files (or uses all if `-a` is not set).  
3. Optionally uses AI to generate commit message.  
4. Classifies or manually sets commit type.  
5. Commits and pushes to the specified or current branch.

---

## Configuration Subpackage (`git_acp.config`)

**Location**: `git_acp/config/__init__.py`, `git_acp/config/constants.py`, `git_acp/config/env_config.py`, `git_acp/config/loader.py`, and `git_acp/config/settings.py`

This subpackage centralizes environment and configuration management.

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

### `git_acp.config.loader.py`

- **Function**: `load_config(config_path: Path) -> dict`  
  Loads configuration from a file and returns it as a dictionary.

### `git_acp.config.settings.py`

- **Grouped Configuration Settings**:  
  - `AI_SETTINGS`: Settings related to AI operations.
  - `GIT_SETTINGS`: Settings related to Git operations.
  - `TERMINAL_SETTINGS`: Settings related to terminal output and formatting.

---

## Git Subpackage (`git_acp.git`)

**Location**: Files under `git_acp/git/`

The Git subpackage is responsible for all Git operations. It has been modularized into several files:

- **`runner.py`**:  
  Executes low-level Git commands and handles errors.

- **`branch.py`**:  
  Manages branch-related operations (e.g., retrieving the current branch, creating/deleting branches).

- **`classification.py`**:  
  Contains logic for commit type classification based on file changes and diff analysis.

- **`commit.py`**:  
  Handles the add, commit, and push workflow.

- **`history.py`**:  
  Retrieves recent commits and performs diff analysis for context.

- **`remote.py`**:  
  Supports operations for adding, removing, or updating remote repositories.

- **`stash.py`**:  
  Implements Git stash functionalities.

- **`status.py`**:  
  Fetches changed files and provides functionality to unstage files.

- **`tag.py`**:  
  Manages Git tag operations.

---

## Utilities Subpackage (`git_acp.utils`)

**Location**: `git_acp/utils/__init__.py`, `git_acp/utils/formatting.py`, and `git_acp/utils/types.py`

This subpackage offers general utility functions and type definitions:

- **Formatting Tools**:  
  `formatting.py` provides styled output for terminal messages using the Rich library.

- **Type and Data Definitions**:  
  `types.py` defines custom types and the `GitConfig` dataclass used across the package.

---

## Command-Line Entry Point (`git_acp.__main__`)

**Location**: `git_acp/__main__.py`

This file provides a Python entry point so the package can be executed from the command line:

```bash
python -m git_acp
```

which directly invokes the CLI defined in `git_acp.cli.cli`.

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
