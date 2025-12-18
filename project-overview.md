---
repo: https://github.com/beecave-homelab/git-acp.git
commit: a59aaa3d9e9fa4e70455fd9c99d62c4a57070f94
updated: 2025-12-02T21:58:00Z
---
<!-- SECTIONS:CLI,API,TESTS -->

# Project Overview | git-acp

`git-acp` is a command-line tool that automates the `git add`, `commit`, and `push` workflow. It offers interactive file selection, AI-powered commit message generation via Ollama, and enforces Conventional Commits standards.

![Language](https://img.shields.io/badge/Python-3.10+-blue)
[![Version](https://img.shields.io/badge/Version-0.18.0-brightgreen)](#version-summary)
[![CLI](https://img.shields.io/badge/CLI-Click-blue)](#cli)
[![Coverage](https://img.shields.io/badge/Coverage-97%25-brightgreen)](#tests)

## Table of Contents

- [Quickstart for Developers](#quickstart-for-developers)
- [Version Summary](#version-summary)
- [Project Features](#project-features)
- [Project Structure](#project-structure)
- [Architecture Highlights](#architecture-highlights)
- [Design Patterns](#design-patterns)
- [Coding Standards](#coding-standards)
- [CLI](#cli)
- [API](#api)
- [Tests](#tests)

## Quickstart for Developers

```bash
# Recommended installation with pipx
pipx install "git+https://github.com/beecave-homelab/git-acp.git"

# Local development setup
git clone https://github.com/beecave-homelab/git-acp.git
cd git-acp
pip install pdm # if not already installed
pdm install -G dev && pdm run git-acp --help
```

### Exporting Requirements Files

Always regenerate the lock-style requirement files from `pyproject.toml` using `pdm`:

```bash
# Production requirements
pdm export --pyproject --no-hashes --prod -o requirements.txt

# Dev / lint / test requirements
pdm export --pyproject --no-hashes -G lint,test -o requirements.dev.txt
```

## Version Summary

| Version | Date       | Type | Key Changes                |
|---------|------------|------|----------------------------|
| 0.18.0  | 02-12-2025 | ✨   | Fix -a flag logic, update eza, enhance tests & UX |
| 0.17.0  | 10-08-2025 | ✨   | Add fallback Ollama server; git ops flattening |
| 0.16.0  | 2025-08-08 | ✨   | Refactors and enhancements; feature work |
| 0.15.1  | 2024-07-08 | 🐛   | Fixed -a flag logic, minor enhancements |
| 0.15.0  | 2025-06-20 | ✨   | Enhanced CLI & version bump |
| 0.14.1  | YYYY-MM-DD | ✨   | Initial project setup      |

## Project Features

- Interactive staging of changed files.
- AI-generated commit messages using Ollama.
- Automatic classification of commit types (feat, fix, etc.).
- Support for Conventional Commits specification.
- Consistent "all files" selection: choose **All files** in the prompt or use `-a .` to stage everything while still listing each file before commit.
- Rich terminal output for better user experience.
- Skipping confirmation prompts for faster workflow.
- Verbose mode for debugging.

## Project Structure

<details><summary>Show tree</summary>

```text
git_acp/
├── __init__.py             # Exposes the package version.
├── __main__.py             # Main entry point, calls the CLI.
├── ai/
│   ├── __init__.py         # Exposes the commit message generation function.
│   ├── ai_utils.py         # Builds commit message prompts and editing helpers.
│   └── client.py           # AIClient with dependency injection for testability.
├── cli/
│   ├── __init__.py         # Exposes CLI, workflow, and interaction classes.
│   ├── cli.py              # Slim CLI entry point using Click (delegates to workflow).
│   ├── interaction.py      # UserInteraction protocol and implementations.
│   └── workflow.py         # GitWorkflow orchestrator for add-commit-push flow.
├── commit/                 # (empty) Intended for future commit-related logic.
├── pr/                     # (empty) Intended for future pull request helpers.
├── config/
│   ├── __init__.py         # Exposes all configuration constants and functions.
│   ├── constants.py        # Defines static configuration values and defaults.
│   └── env_config.py       # Manages loading of environment variables.
├── git/
│   ├── __init__.py         # Exposes all public Git operation functions (facade).
│   ├── classification.py   # Classifies commit types based on file changes.
│   ├── core.py             # Core git utilities and error handling.
│   ├── diff.py             # Diff generation and formatting.
│   ├── git_operations.py   # Compatibility layer for testable git helpers.
│   ├── history.py          # Commit history and analysis utilities.
│   ├── management.py       # Branch and repository management.
│   ├── operations.py       # Re-exports public functions (facade pattern).
│   └── staging.py          # File staging and change detection.
└── utils/
    ├── __init__.py         # Exposes utility functions and types.
    ├── formatting.py       # Provides styled terminal output functions.
    └── types.py            # Defines custom data types and type aliases.

tests/
├── __init__.py
├── ai/                     # AIClient and AI utilities tests.
├── cli/                    # CLI entry point and GitWorkflow tests.
├── config/                 # Configuration tests.
├── git/                    # Git operations tests.
└── utils/                  # Utility function tests.
```

</details>

## Architecture Highlights

- **CLI Layer**: Built with `click`, delegates to `GitWorkflow` orchestrator.
- **Workflow Orchestration**: `GitWorkflow` coordinates add-commit-push operations with injected dependencies.
- **User Interaction Protocol**: `UserInteraction` protocol abstracts `questionary`/`rich` for testability.
- **Dependency Injection**: `AIClient` and `GitWorkflow` accept injected dependencies for testing.
- **Modular Design**: Separate packages for AI, CLI, git operations, and configuration.
- **SOLID Principles**: Single Responsibility (workflow vs CLI), Dependency Inversion (protocols).

### Component Interaction Diagram

```mermaid
classDiagram
    direction TB
    %% Styling
    classDef cli fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef work fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef ai fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef git fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef config fill:#eceff1,stroke:#37474f,stroke-width:2px;

    namespace CLI_Layer {
        class cli_py:::cli {
            Click Entry Point
        }
    }
    
    namespace Orchestration_Layer {
        class GitWorkflow:::work {
            Coordinator
        }
        class UserInteraction:::work {
            <<Protocol>>
        }
    }
    
    namespace AI_Layer {
        class AIClient:::ai {
            OpenAI Wrapper
        }
        class ai_utils:::ai {
            Prompt Builders
        }
    }
    
    namespace Git_Layer {
        class operations_py:::git {
            <<Facade>>
        }
        class core_py:::git
        class staging_py:::git
        class diff_py:::git
        class classification_py:::git
        class history_py:::git
        class management_py:::git
    }
    
    namespace Config {
        class constants_py:::config
        class env_config_py:::config
    }

    cli_py --> GitWorkflow
    GitWorkflow --> UserInteraction
    GitWorkflow --> operations_py
    GitWorkflow --> ai_utils
    ai_utils --> AIClient
    operations_py --> core_py
    operations_py --> staging_py
    operations_py --> diff_py
    operations_py --> classification_py
    operations_py --> history_py
    operations_py --> management_py
    AIClient ..> constants_py
    constants_py ..> env_config_py
```

### Data Flow Overview

High-level flow when running `git-acp --ollama`:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CLI
    participant Workflow as GitWorkflow
    participant UI as UserInteraction
    participant Ops as GitOps
    participant AI as AILayer
    participant Ollama as OllamaServer

    Note over User, CLI: Input: git-acp --ollama

    User->>CLI: invokes
    CLI->>Workflow: delegates
    Workflow->>UI: select files
    Workflow->>Ops: stage files
    Workflow->>AI: generate message
    AI->>Ollama: AI request
    Ollama-->>AI: response
    AI-->>Workflow: message
    Workflow->>UI: select type and confirm
    Workflow->>Ops: commit and push
    UI-->>User: done
```

### Deep Dive: GitWorkflow

The orchestrator that coordinates the entire add-commit-push workflow.

```mermaid
classDiagram
    direction TB
    %% Styling
    classDef core fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef inject fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef part fill:#fff3e0,stroke:#e65100,stroke-width:2px;

    class GitWorkflow:::core {
        +run()
        -_handle_file_selection()
        -_handle_branch_detection()
        -_handle_git_add()
        -_handle_commit_message()
        -_handle_commit_type()
        -_handle_confirmation()
        -_handle_commit()
        -_handle_push()
    }

    class GitConfig:::inject {
        +files: str
        +message: str
        +branch: str
        +use_ollama: bool
        +skip_confirmation: bool
        +verbose: bool
        +prompt_type: str
    }

    class UserInteraction:::inject {
        <<interface>>
        +select_files()
        +select_commit_type()
        +confirm()
    }

    class GitOps:::part {
        +get_changed_files()
        +git_add()
        +git_commit()
        +git_push()
    }

    class AIUtils:::part {
        +generate_commit_message()
    }

    class Classification:::part {
        +classify_commit_type()
    }

    GitWorkflow ..> GitConfig : uses
    GitWorkflow --> UserInteraction : injected
    GitWorkflow --> GitOps : calls
    GitWorkflow --> AIUtils : calls
    GitWorkflow --> Classification : calls
```

### Deep Dive: GitOps (Facade)

The `operations.py` facade re-exports functions from internal modules.

```mermaid
classDiagram
    direction TB
    %% Styling
    classDef facade fill:#e8f5e9,stroke:#1b5e20,stroke-width:4px;
    classDef module fill:#fff8e1,stroke:#ff6f00,stroke-width:1px;
    classDef sub fill:#eceff1,stroke:#37474f,stroke-width:1px,stroke-dasharray: 5 5;

    class GitOps:::facade {
        <<Facade>>
        operations.py
    }

    class Core:::module {
        core.py
        +GitError
        +run_git_command()
    }
    
    class Staging:::module {
        staging.py
        +git_add()
        +git_commit()
        +git_push()
    }
    
    class Diff:::module {
        diff.py
        +get_diff()
    }
    
    class History:::module {
        history.py
        +get_recent_commits()
    }

    class Management:::module {
        management.py
        +create_branch()
    }

    class Subprocess:::sub {
        git CLI
    }

    GitOps ..> Core : re-exports
    GitOps ..> Staging : re-exports
    GitOps ..> Diff : re-exports
    GitOps ..> History : re-exports
    GitOps ..> Management : re-exports
    Core ..> Subprocess : executes
```

### Deep Dive: AI Layer

AI-powered commit message generation with fallback support.

```mermaid
classDiagram
    direction TB
    %% Styling
    classDef main fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef ext fill:#fce4ec,stroke:#880e4f,stroke-width:2px;
    classDef conf fill:#f3e5f5,stroke:#4a148c,stroke-width:1px;

    class AIUtils:::main {
        +generate_commit_message()
        +get_commit_context()
        +create_simple_prompt()
        +create_advanced_prompt()
    }

    class AIClient:::main {
        +chat_completion()
        -_openai_client
        -_progress_factory
    }

    class GitOps:::main {
        +get_diff()
        +get_recent_commits()
    }

    class Config:::conf {
        +DEFAULT_AI_MODEL
        +DEFAULT_BASE_URL
    }

    class OllamaServer:::ext {
        localhost:11434
    }
    
    class FallbackServer:::ext {
        diffsense.onrender.com
    }

    AIUtils --> AIClient : creates
    AIUtils ..> GitOps : fetches context
    AIClient ..> Config : reads settings
    AIClient --> OllamaServer : primary
    AIClient --> FallbackServer : fallback
```

### Deep Dive: UserInteraction

Protocol-based abstraction for testable user I/O.

```mermaid
classDiagram
    direction TB
    %% Styling
    classDef proto fill:#fff3e0,stroke:#e65100,stroke-width:2px,font-style:italic;
    classDef impl fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef lib fill:#f5f5f5,stroke:#616161,stroke-width:1px;

    class UserInteraction:::proto {
        <<Protocol>>
        +select_files()
        +select_commit_type()
        +confirm()
        +print_message()
        +print_error()
        +print_panel()
    }

    class RichQuestionaryInteraction:::impl {
        +select_files()
        +select_commit_type()
    }

    class TestInteraction:::impl {
        +select_files()
        +select_commit_type()
    }

    class Rich:::lib {
        Panel, Confirm
    }

    class Questionary:::lib {
        checkbox, text
    }

    UserInteraction <|.. RichQuestionaryInteraction : implements
    UserInteraction <|.. TestInteraction : implements
    RichQuestionaryInteraction ..> Rich : uses
    RichQuestionaryInteraction ..> Questionary : uses
```

## Design Patterns

### Protocol Pattern (Structural Typing)

The `UserInteraction` protocol in `interaction.py` defines an interface for user I/O:

```python
class UserInteraction(Protocol):
    def select_files(self, changed_files: set[str]) -> str: ...
    def select_commit_type(self, suggested_type: CommitType, config: GitConfig) -> CommitType: ...
    def confirm(self, message: str) -> bool: ...
    def print_message(self, message: str) -> None: ...
    def print_error(self, error_msg: str, suggestion: str, title: str) -> None: ...
    def print_panel(self, content: str, title: str, style: str) -> None: ...
```

**Implementations:**

- `RichQuestionaryInteraction` — Production implementation using Rich + Questionary.
- `TestInteraction` — Test double with canned responses for unit testing.

### Dependency Injection

`GitWorkflow` and `AIClient` accept injected dependencies:

```python
# GitWorkflow accepts UserInteraction
class GitWorkflow:
    def __init__(self, config: GitConfig, interaction: UserInteraction, ...) -> None:

# AIClient accepts OpenAI client and progress factory
class AIClient:
    def __init__(self, config: OptionalConfig = None, *,
                 _openai_client: OpenAI | None = None,
                 _progress_factory: ProgressFactory | None = None) -> None:
```

### Facade Pattern

The `git/__init__.py` and `git/operations.py` modules expose a unified API:

```python
# git/__init__.py re-exports all public functions
from git_acp.git.operations import (
    GitError, get_changed_files, get_current_branch, get_diff,
    git_add, git_commit, git_push, run_git_command, ...
)
```

Internal modules (`core.py`, `staging.py`, `diff.py`, etc.) remain implementation details.

### Dataclass Configuration

`GitConfig` in `utils/types.py` uses `@dataclass` for immutable configuration:

```python
@dataclass
class GitConfig:
    files: str = "."
    message: str = "Automated commit"
    branch: str | None = None
    use_ollama: bool = False
    interactive: bool = False
    skip_confirmation: bool = False
    verbose: bool = False
    prompt_type: str = "advanced"
```

### Enum for Commit Types

`CommitType` in `classification.py` uses `Enum` with a factory method:

```python
class CommitType(Enum):
    FEAT = "feat"
    FIX = "fix"
    # ...

    @classmethod
    def from_str(cls, value: str) -> "CommitType":
        # Converts string to enum, raises GitError on invalid input
```

## Coding Standards

### Linting & Formatting (Ruff)

Configured in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["F", "E", "W", "N", "I", "D", "DOC", "TID", "UP", "FA"]

[tool.ruff.lint.pydocstyle]
convention = "google"
```

**Key rules enforced:**

- **F** (Pyflakes): No undefined names, unused imports.
- **E/W** (pycodestyle): PEP 8 spacing, indentation.
- **N** (pep8-naming): `snake_case` functions, `PascalCase` classes.
- **I** (isort): Sorted, grouped imports.
- **D/DOC** (pydocstyle): Google-style docstrings.
- **UP** (pyupgrade): Modern Python syntax (f-strings, PEP 585 generics).
- **FA** (future-annotations): `from __future__ import annotations`.

### SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **SRP** | `cli.py` handles CLI parsing only; `workflow.py` handles orchestration. |
| **OCP** | `UserInteraction` protocol allows new implementations without modifying `GitWorkflow`. |
| **LSP** | `TestInteraction` is substitutable for `RichQuestionaryInteraction`. |
| **ISP** | Protocol methods are minimal and focused. |
| **DIP** | `GitWorkflow` depends on `UserInteraction` abstraction, not concrete classes. |

### Testing Conventions

- **Naming**: `test_<unit>__<expected_behavior>()`
- **Fixtures**: Use `pytest` fixtures for reusable setup.
- **Mocking**: Patch at the module boundary (e.g., `git_acp.git.git_operations.run_git_command`).
- **Coverage**: Target ≥85% line coverage with branch coverage enabled.

### Type Hints

All public functions and methods use type hints:

```python
def get_changed_files(
    config: OptionalConfig = None, staged_only: bool = False
) -> set[str]: ...
```

Type aliases in `utils/types.py`:

```python
OptionalConfig = GitConfig | None
PromptType = Literal["simple", "advanced"]
DiffType = Literal["staged", "unstaged"]
```

## CLI

The main entry point is `git_acp.cli.cli.main`. It provides a set of options to control the git workflow.

**Options:**

- `-a, --add`: Specify files to stage.
- `-m, --message`: Provide a custom commit message.
- `-b, --branch`: Target branch for push.
- `-t, --type`: Manually specify commit type.
- `-o, --ollama`: Use AI to generate commit message.
- `-i, --interactive`: Interactively edit AI-generated message.
- `-nc, --no-confirm`: Skip confirmation prompts.
- `-v, --verbose`: Enable verbose output.
- `-p, --prompt-type`: Select AI prompt complexity.

## API

> This project does not expose a public API. It is intended to be used as a command-line tool.

## Tests

Test coverage: **97%** (branch coverage enabled).

**Test Structure:**

- `tests/ai/` — AIClient and AI utilities tests (96% coverage on client.py)
- `tests/cli/` — CLI entry point and GitWorkflow tests (85-87% coverage)
- `tests/git/` — Git operations tests (92-98% coverage)
- `tests/config/` — Configuration tests
- `tests/utils/` — Utility function tests

**Run Tests:**

```bash
pdm run pytest --cov=git_acp --cov-branch --cov-report=term-missing
```

**Always update this file when code or configuration changes.**
