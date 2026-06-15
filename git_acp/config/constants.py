"""Constants module for git-acp package configuration.

This module contains all configuration constants used throughout the git-acp package.
Constants are organized by their functional category for better maintainability.

Categories:
    - AI Configuration: Settings for AI-powered commit message generation
    - Git Configuration: Basic git operation settings
    - File Patterns: Patterns for file exclusion in git operations
    - Commit Types: Pattern matching for automatic commit type classification
    - Formatting: Terminal output formatting settings
    - Terminal: Terminal-specific configurations
"""

from pathlib import Path
from typing import Final

from git_acp.config.env_config import get_config_dir, get_env, load_env_config

# Load environment variables at module import
load_env_config()

# Path Configuration
# These are primarily used by setup scripts and for locating the user .env file.
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
USER_CONFIG_DIR: Final[Path] = get_config_dir()
USER_ENV_FILE: Final[Path] = USER_CONFIG_DIR / ".env"

# AI Configuration
# Settings for OpenAI-compatible API interaction
DEFAULT_AI_MODEL: Final[str] = get_env("GIT_ACP_AI_MODEL", "mevatron/diffsense:1.5b")
DEFAULT_TEMPERATURE: Final[float] = get_env("GIT_ACP_TEMPERATURE", 0.7, float)
DEFAULT_BASE_URL: Final[str] = get_env("GIT_ACP_BASE_URL", "http://localhost:11434/v1")
DEFAULT_FALLBACK_BASE_URL: Final[str] = get_env(
    "GIT_ACP_FALLBACK_BASE_URL", "https://diffsense.onrender.com/v1"
)
DEFAULT_API_KEY: Final[str] = get_env("GIT_ACP_API_KEY", "ollama")
DEFAULT_PROMPT_TYPE: Final[str] = get_env(
    "GIT_ACP_PROMPT_TYPE", "advanced"
)  # Options: "simple" or "advanced"
DEFAULT_AI_TIMEOUT: Final[float] = get_env(
    "GIT_ACP_AI_TIMEOUT", 120.0, float
)  # Timeout in seconds for AI requests
DEFAULT_CONTEXT_WINDOW: Final[int] = get_env(
    "GIT_ACP_CONTEXT_WINDOW", 8192, int
)  # Context window size in tokens for Ollama requests

# Prompt Context Configuration
# Context ratios determine what portion of the window is used for prompts vs response
SIMPLE_PROMPT_CONTEXT_RATIO: Final[float] = get_env(
    "GIT_ACP_SIMPLE_CONTEXT_RATIO", 0.65, float
)  # 65% of context window for simple prompts (local-first)
ADVANCED_PROMPT_CONTEXT_RATIO: Final[float] = get_env(
    "GIT_ACP_ADVANCED_CONTEXT_RATIO", 0.80, float
)  # 80% of context window for advanced prompts
MIN_CHANGES_CONTEXT: Final[int] = get_env(
    "GIT_ACP_MIN_CHANGES_CONTEXT", 2000, int
)  # Minimum tokens reserved for staged changes

# Git Configuration
# Basic settings for git operations
DEFAULT_BRANCH: Final[str] = get_env("GIT_ACP_DEFAULT_BRANCH", "main")
DEFAULT_REMOTE: Final[str] = get_env("GIT_ACP_DEFAULT_REMOTE", "origin")
DEFAULT_NUM_RECENT_COMMITS: Final[int] = get_env("GIT_ACP_NUM_RECENT_COMMITS", 3, int)
DEFAULT_NUM_RELATED_COMMITS: Final[int] = get_env("GIT_ACP_NUM_RELATED_COMMITS", 3, int)
MAX_DIFF_PREVIEW_LINES: Final[int] = get_env("GIT_ACP_MAX_DIFF_PREVIEW_LINES", 10, int)
DEFAULT_AUTO_GROUP_MAX_NON_TYPE_GROUPS: Final[int] = get_env(
    "GIT_ACP_AUTO_GROUP_MAX_NON_TYPE_GROUPS", 5, int
)

# File patterns to exclude from git operations
# These patterns match common build artifacts and environment-specific files
EXCLUDED_PATTERNS: Final[list[str]] = [
    "__pycache__",  # Python bytecode cache
    ".pyc",  # Compiled Python files
    ".pyo",  # Optimized Python files
    ".pyd",  # Python DLL files
    "/.env$",  # Only exact .env files, not .env.example etc.
    ".venv",  # Virtual environment directory
    "node_modules",  # Node.js dependencies
]

# Commit type definitions with their corresponding emojis
COMMIT_TYPES: Final[dict[str, str]] = {
    "FEAT": get_env("GIT_ACP_COMMIT_TYPE_FEAT", "feat ✨"),
    "FIX": get_env("GIT_ACP_COMMIT_TYPE_FIX", "fix 🐛"),
    "DOCS": get_env("GIT_ACP_COMMIT_TYPE_DOCS", "docs 📝"),
    "STYLE": get_env("GIT_ACP_COMMIT_TYPE_STYLE", "style 💎"),
    "REFACTOR": get_env("GIT_ACP_COMMIT_TYPE_REFACTOR", "refactor ♻️"),
    "TEST": get_env("GIT_ACP_COMMIT_TYPE_TEST", "test 🧪"),
    "CHORE": get_env("GIT_ACP_COMMIT_TYPE_CHORE", "chore 📦"),
    "REVERT": get_env("GIT_ACP_COMMIT_TYPE_REVERT", "revert ⏪"),
    "BUILD": get_env("GIT_ACP_COMMIT_TYPE_BUILD", "build 🏗️"),
    "CI": get_env("GIT_ACP_COMMIT_TYPE_CI", "ci 🤖"),
    "PERF": get_env("GIT_ACP_COMMIT_TYPE_PERF", "perf ⚡"),
}

# File path patterns for commit type classification (highest priority)
# These patterns match against changed file paths for accurate classification
FILE_PATH_PATTERNS: Final[dict[str, list[str]]] = {
    "test": ["tests/", "test/", "test_", "_test.py", ".test.", "conftest.py"],
    "docs": ["docs/", "doc/", "README", "CHANGELOG", "VERSIONS", "LICENSE"],
    "build": [
        "Dockerfile",
        "docker-compose",
        "docker-compose.yml",
        ".dockerignore",
        "Makefile",
        "tox.ini",
        "noxfile.py",
    ],
    "ci": [
        ".github/workflows/",
        ".gitlab-ci.yml",
        "Jenkinsfile",
        ".circleci/",
        ".travis.yml",
        "azure-pipelines.yml",
    ],
    "perf": [
        "benchmark",
        "profiling",
        "performance",
    ],
    "chore": [
        ".gitignore",
        "requirements",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        ".pre-commit",
        ".env",
    ],
    "style": [".pylintrc", ".flake8", "ruff.toml", ".prettierrc", ".eslintrc"],
}

# Keyword patterns for commit message classification (medium priority)
# Used when file paths don't provide a clear signal
COMMIT_TYPE_PATTERNS: Final[dict[str, list[str]]] = {
    "test": ["test", "tests", "testing", "coverage"],
    "docs": ["documentation", "readme", "docstring"],
    "fix": [
        "fix",
        "bug",
        "patch",
        "issue",
        "error",
        "crash",
        "resolve",
        "correct",
        "compatibility",
        "prevent breaking",
    ],
    "feat": [
        "feature",
        "introduce",
        "introduces",
        "introduced",
        "implement",
        "implements",
        "create",
        "support",
        "enable",
        "allow",
        "option",
        "flag",
    ],
    "refactor": ["refactor", "restructure", "cleanup", "clean up", "reorganize"],
    "chore": [
        "bump",
        "version",
        "release",
        "dependency",
        "dependencies",
        "changelog",
        "gitignore",
        "default value",
        "configuration",
        "config",
        "env var",
        "environment variable",
    ],
    "build": [
        "build",
        "compile",
        "docker",
        "container",
        "image",
        "artifact",
        "package",
        "bundle",
        "webpack",
        "rollup",
    ],
    "ci": [
        "ci",
        "cd",
        "pipeline",
        "workflow",
        "continuous integration",
        "continuous delivery",
        "continuous deployment",
        "github actions",
        "jenkins",
        "travis",
        "circleci",
    ],
    "perf": [
        "performance",
        "perf",
        "optimize",
        "optimise",
        "speed",
        "latency",
        "throughput",
        "memory usage",
        "benchmark",
        "slow",
        "cache",
        "caching",
    ],
    "style": [
        "format",
        "formatting",
        "reformat",
        "format code",
        "whitespace",
        "lint",
        "linting",
        "prettier",
    ],
}

# File category patterns for the scoring classifier.
# Maps FileCategory names to file path patterns used by classify_file_category().
FILE_CATEGORY_PATTERNS: Final[dict[str, list[str]]] = {
    "DEPENDENCY": [
        "requirements",
        "Pipfile",
        "Pipfile.lock",
        "uv.lock",
        "poetry.lock",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Gemfile.lock",
        "go.sum",
        "Cargo.lock",
    ],
    "GENERATED": [
        "__pycache__",
        ".pyc",
        ".pyo",
        ".pyd",
        ".egg-info",
        "dist/",
        "build/",
        ".eggs/",
        "*.pyc",
        "node_modules",
        ".coverage",
        "coverage.xml",
        "htmlcov/",
        ".mypy_cache/",
    ],
    "CI": [
        ".github/workflows/",
        ".gitlab-ci.yml",
        "Jenkinsfile",
        ".circleci/",
        ".travis.yml",
        "azure-pipelines.yml",
    ],
    "TEST": [
        "tests/",
        "test/",
        "test_",
        "_test.py",
        ".test.",
        "conftest.py",
        "spec/",
        "__tests__/",
    ],
    "DOCS": [
        "docs/",
        "doc/",
        "README",
        "CHANGELOG",
        "VERSIONS",
        "LICENSE",
        ".md",
    ],
    "BUILD": [
        "Makefile",
        "Dockerfile",
        "docker-compose",
        "docker-compose.yml",
        ".dockerignore",
        "tox.ini",
        "noxfile.py",
    ],
    "CONFIG": [
        ".gitignore",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        ".pre-commit",
        ".env",
        ".flake8",
        ".pylintrc",
        "ruff.toml",
        ".prettierrc",
        ".eslintrc",
        ".editorconfig",
        ".babelrc",
        "tsconfig.json",
    ],
    "STYLE": [
        ".pylintrc",
        ".flake8",
        "ruff.toml",
        ".prettierrc",
        ".eslintrc",
    ],
}

# Signal layer weights for the scoring classifier.
# All layers start at 1.0 — priority is enforced by structural flow,
# not numeric differentiation. Tune from real misclassification data.
SIGNAL_LAYER_WEIGHTS: Final[dict[str, float]] = {
    "message_prefix": 1.0,
    "file_category": 1.0,
    "message_keyword": 1.0,
    "diff_keyword": 1.0,
}

# Formatting Configuration
# Color settings for terminal output using rich library
COLORS: Final[dict[str, str]] = {
    "debug_header": get_env("GIT_ACP_DEBUG_HEADER_COLOR", "blue"),
    "debug_value": get_env("GIT_ACP_DEBUG_VALUE_COLOR", "cyan"),
    "info": get_env("GIT_ACP_INFO_COLOR", "cyan"),
    "success": get_env("GIT_ACP_SUCCESS_COLOR", "green"),
    "warning": get_env("GIT_ACP_WARNING_COLOR", "yellow"),
    "status": get_env("GIT_ACP_STATUS_COLOR", "bold green"),
    "error": get_env("GIT_ACP_ERROR_COLOR", "bold red"),
    # AI message formatting
    "ai_message_header": get_env("GIT_ACP_AI_MESSAGE_HEADER_COLOR", "bold yellow"),
    "ai_message_border": get_env("GIT_ACP_AI_MESSAGE_BORDER_COLOR", "yellow"),
    "key_combination": get_env("GIT_ACP_KEY_COMBINATION_COLOR", "cyan"),
    "instruction_text": get_env("GIT_ACP_INSTRUCTION_TEXT_COLOR", "dim"),
    # Text style formatting
    "bold": get_env("GIT_ACP_BOLD_COLOR", "dim"),
}

MAX_DEBUG_VALUE_CHARS: Final[int] = get_env(
    "GIT_ACP_MAX_DEBUG_VALUE_CHARS", 1200, int
)  # Maximum length of debug values before truncation

# Questionary style configuration
QUESTIONARY_STYLE: Final[list[tuple[str, str]]] = [
    ("qmark", "fg:yellow bold"),
    ("question", "bold"),
    ("pointer", "fg:yellow bold"),
    ("highlighted", "fg:yellow bold"),
    ("selected", "fg:green"),
]

# Terminal Configuration
TERMINAL_WIDTH: Final[int] = get_env(
    "GIT_ACP_TERMINAL_WIDTH", 100, int
)  # Maximum width for formatted output
