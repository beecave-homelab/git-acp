# AGENTS.md

## Setup & Commands

### Install

```bash
# Recommended (developer setup)
pip install pdm
pdm install -G lint,test
```

```bash
# Alternative: local venv (no PDM)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

### Run / Dev

```bash
# CLI help
pdm run git-acp --help
```

```bash
# Example run (interactive)
pdm run git-acp
```

### Tests

```bash
pdm run test
```

```bash
# Coverage output (xml + terminal)
pdm run test-cov
```

### Lint / Format / Typecheck

```bash
pdm run lint
pdm run format
pdm run fix  # lint + autofix
```

### Build

```bash
pdm build
```

### Other Tools

```bash
# Setup user config file
pdm run setup-config
```

```bash
# Local CI pipeline (fix/format/tests/coverage/docstrings)
./scripts/local-ci.sh
```

## Project Structure

```text
.git-acp/
├── git_acp/                   # Python package
│   ├── ai/                    # AI client + prompt utils
│   ├── cli/                   # Click CLI + workflow orchestration
│   ├── config/                # Env + constants
│   ├── git/                   # Git operations + classification
│   └── utils/                 # Formatting + types
├── scripts/                   # Dev scripts (setup-config, local-ci)
├── docs/                      # Usage + API docs
├── tests/                     # Pytest suite
├── pyproject.toml             # PDM config + scripts
└── .env.example               # Config template
```

**Key files**:

- `git_acp/cli/cli.py`: CLI entry point (Click)
- `git_acp/cli/workflow.py`: `GitWorkflow` orchestrator
- `git_acp/ai/ai_utils.py`: AI prompt and context flow
- `git_acp/git/operations.py`: Public Git facade
- `git_acp/config/constants.py`: Defaults + env wiring

**Path aliases**: none.

## Tech Stack

### Core

- Python `>=3.10,<3.14` (see `pyproject.toml`)
- PDM for packaging and scripts

### CLI & UX

- `click` for CLI parsing
- `rich` for styled output
- `questionary` for interactive prompts

### AI Integration

- `openai` client for OpenAI-compatible APIs (Ollama/local/cloud)
- `python-dotenv` for environment configuration

### Development

- `ruff` for linting/formatting
- `pytest` + `pytest-cov` for tests
- `interrogate` for docstring coverage

## Architecture & Patterns

### CLI Workflow Orchestration

- `git_acp.cli.cli.main` is a thin Click wrapper that forwards to `GitWorkflow`.
- `GitWorkflow` coordinates file selection, staging, AI message generation, and push.
- `UserInteraction` protocol in `git_acp/cli/interaction.py` abstracts I/O for testability.

### AI Layer

- Prompt generation is centralized in `git_acp/ai/ai_utils.py`.
- Two prompt types: `simple` (fast, minimal context) and `advanced` (repo-aware).
- Context window and timeouts are configurable via env vars (see `.env.example`).

### Git Operations

- `git_acp/git/operations.py` acts as a facade re-exporting internal modules.
- Internal modules isolate concerns: `staging.py`, `diff.py`, `history.py`, `management.py`.

### Configuration

- Environment values are loaded in `git_acp/config/env_config.py`.
- Defaults and env mapping live in `git_acp/config/constants.py`.
- User config file lives at `~/.config/git-acp/.env`.

## Code Style & Patterns

### Python

#### Coding Rules

- Follow Ruff config in `pyproject.toml` (line length 88, Google-style docstrings).
- Use type hints for all public functions and methods (see `git_acp/utils/types.py`).
- Prefer small, focused modules; avoid side effects in imports (see `git_acp/cli/cli.py`).
- Keep CLI concerns in `git_acp/cli/` and Git operations in `git_acp/git/` (see `git_acp/cli/workflow.py`, `git_acp/git/operations.py`).
- Use dependency injection for I/O and external services (see `git_acp/ai/client.py`, `git_acp/cli/workflow.py`).
- Prefer pure functions for classification/formatting logic; keep I/O at boundaries (see `git_acp/git/classification.py`, `git_acp/utils/formatting.py`).
- Raise `GitError` for user-facing failures (see `git_acp/git/core.py`).
- Keep config reads centralized in `git_acp/config/constants.py` + `git_acp/config/env_config.py`.

#### SOLID Principles (project conventions)

- **SRP**: `cli.py` handles Click parsing only; workflow logic lives in `workflow.py` (see `git_acp/cli/cli.py`, `git_acp/cli/workflow.py`).
- **OCP**: `UserInteraction` protocol allows new UI implementations without changing workflow (see `git_acp/cli/interaction.py`).
- **LSP**: `TestInteraction` must be substitutable for `RichQuestionaryInteraction` in tests (see `git_acp/cli/interaction.py`).
- **ISP**: `UserInteraction` stays minimal (only required interaction methods) (see `git_acp/cli/interaction.py`).
- **DIP**: `GitWorkflow` depends on the `UserInteraction` abstraction, not concrete UI classes (see `git_acp/cli/workflow.py`).

#### Formatting Rules

- Run `pdm run format` (Ruff formatter) before commits (see `pyproject.toml`).
- Enforced line length: 88 (see `pyproject.toml`).
- Quote style: double quotes; indent style: spaces (see `pyproject.toml`).
- Line endings: LF (see `pyproject.toml`).
- Import ordering: Ruff/Isort rules (group stdlib → third-party → local) (see `pyproject.toml`).
- Use `from __future__ import annotations` in new modules (Ruff `FA` rule) (see `pyproject.toml`).
- Docstrings: Google-style, required for public modules/classes/functions (see `pyproject.toml`).

### Testing

- `pytest` tests live in `tests/` with feature-based subfolders.
- Patch at module boundaries (see `docs/tests/test_plan.md`).

## Git / PR Workflow

- Default branches: `main`, `dev` (see `.github/workflows/pr-ci.yaml`).
- CI runs: `pdm run lint --fix`, `pdm run format`, `pdm run test`, `pdm run test-cov`.
- Use Conventional Commits (see commit type enum in `git_acp/git/classification.py`).

## Boundaries

### ✅ Always

- Run `pdm run lint` and `pdm run test` before PRs.
- Keep CLI behavior in `git_acp/cli/` and git ops in `git_acp/git/`.
- Update `.env.example` when new env vars are introduced.
- Keep AI prompt changes in `git_acp/ai/ai_utils.py`.
- Update `project-overview.md` when architecture or CLI options change.

### ⚠️ Ask First

- Changing default CLI flags or existing command semantics.
- Modifying `GitWorkflow` orchestration order or skipping confirmations.
- Adjusting AI prompt structure, context ratios, or token budgeting.
- Adding new external dependencies or heavy AI models.
- Changing configuration file locations or env var names.

### 🚫 Never

- Commit secrets or real API keys.
- Edit `requirements*.txt` directly (regenerate via PDM export).
- Bypass `UserInteraction` protocol to write direct terminal I/O.
- Modify `pdm.lock` manually.

## Common Tasks

### 1) Add a new CLI option

1. Update Click options in `git_acp/cli/cli.py`.
2. Thread the value into `GitConfig` (`git_acp/utils/types.py`).
3. Use it in `GitWorkflow` (`git_acp/cli/workflow.py`).
4. Add or update tests in `tests/cli/`.
5. Verify: `pdm run test` passes and `git-acp --help` shows the new flag.

### 2) Adjust AI prompt behavior

1. Modify prompt creation in `git_acp/ai/ai_utils.py`.
2. Update `.env.example` for new settings (if added).
3. Add/update tests in `tests/ai/`.
4. Verify: run `pdm run test` and a manual `git-acp -o` run.

### 3) Add new commit type

1. Update `COMMIT_TYPES` and patterns in `git_acp/config/constants.py`.
2. Update `CommitType` enum in `git_acp/git/classification.py`.
3. Adjust documentation in `docs/usage/basic_usage.md`.
4. Add tests in `tests/git/`.
5. Verify: commit type suggestion works in interactive flow.

### 4) Regenerate requirements files

```bash
pdm export --pyproject --no-hashes --prod -o requirements.txt
pdm export --pyproject --no-hashes -G lint,test -o requirements.dev.txt
```

Verify: diffs only in requirements files and lockfile if deps changed.

### 5) Run full local CI

```bash
./scripts/local-ci.sh
```

Verify: `ci-output.log` ends with “Local CI check successful.”

## Troubleshooting

### Installation

**`pipx install` fails or package not found** → upgrade pip and retry (see `docs/getting_started/installation.md`).

### AI Connection

**`git-acp -o` hangs or fails** → ensure Ollama is running (`ollama serve`) and `GIT_ACP_BASE_URL` points to the correct endpoint.

### Questionary UI error on Debian

**`'VSplit' object has no attribute 'content'`** → install `prompt-toolkit<3.0.50` or upgrade `git-acp` (see `docs/getting_started/installation.md`).

### Git errors

**Push rejected** → resolve conflicts manually, then re-run `git-acp`.

### Local CI script errors

**`pdm run fix` fails** → run `pdm run lint` and address Ruff errors first.
