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

from typing import Dict, List, Final
from git_acp.config.env_config import get_env, load_env_config

# Load environment variables at module import
load_env_config()

# AI Configuration
# Settings for OpenAI-compatible API interaction
DEFAULT_AI_MODEL: Final[str] = get_env('GIT_ACP_AI_MODEL', "mevatron/diffsense:1.5b")
DEFAULT_PR_AI_MODEL: Final[str] = get_env('GIT_ACP_PR_AI_MODEL', "qwen2.5:3b-instruct")  # Larger model for PR descriptions
DEFAULT_TEMPERATURE: Final[float] = get_env('GIT_ACP_TEMPERATURE', 0.7, float)
DEFAULT_BASE_URL: Final[str] = get_env('GIT_ACP_BASE_URL', "http://localhost:11434/v1")
DEFAULT_API_KEY: Final[str] = get_env('GIT_ACP_API_KEY', "ollama")
DEFAULT_PROMPT_TYPE: Final[str] = get_env('GIT_ACP_PROMPT_TYPE', "advanced")  # Options: "simple" or "advanced"
DEFAULT_AI_TIMEOUT: Final[float] = get_env('GIT_ACP_AI_TIMEOUT', 120.0, float)  # Timeout in seconds for AI requests

# GitHub Configuration
# Settings for GitHub API interaction
GITHUB_TOKEN: Final[str] = get_env('GITHUB_TOKEN', "")  # Required for PR creation

# Git Configuration
# Basic settings for git operations
DEFAULT_BRANCH: Final[str] = get_env('GIT_ACP_DEFAULT_BRANCH', "main")
DEFAULT_REMOTE: Final[str] = get_env('GIT_ACP_DEFAULT_REMOTE', "origin")
DEFAULT_NUM_RECENT_COMMITS: Final[int] = get_env('GIT_ACP_NUM_RECENT_COMMITS', 3, int)
DEFAULT_NUM_RELATED_COMMITS: Final[int] = get_env('GIT_ACP_NUM_RELATED_COMMITS', 3, int)
MAX_DIFF_PREVIEW_LINES: Final[int] = get_env('GIT_ACP_MAX_DIFF_PREVIEW_LINES', 10, int)

# File patterns to exclude from git operations
# These patterns match common build artifacts and environment-specific files
EXCLUDED_PATTERNS: Final[List[str]] = [
    '__pycache__',  # Python bytecode cache
    '.pyc',         # Compiled Python files
    '.pyo',         # Optimized Python files
    '.pyd',         # Python DLL files
    '/.env$',       # Only exact .env files, not .env.example etc.
    '.venv',        # Virtual environment directory
    'node_modules'  # Node.js dependencies
]

# Commit type definitions with their corresponding emojis
COMMIT_TYPES: Final[Dict[str, str]] = {
    'FEAT': get_env('GIT_ACP_COMMIT_TYPE_FEAT', "feat ✨"),
    'FIX': get_env('GIT_ACP_COMMIT_TYPE_FIX', "fix 🐛"),
    'DOCS': get_env('GIT_ACP_COMMIT_TYPE_DOCS', "docs 📝"),
    'STYLE': get_env('GIT_ACP_COMMIT_TYPE_STYLE', "style 💎"),
    'REFACTOR': get_env('GIT_ACP_COMMIT_TYPE_REFACTOR', "refactor ♻️"),
    'TEST': get_env('GIT_ACP_COMMIT_TYPE_TEST', "test 🧪"),
    'CHORE': get_env('GIT_ACP_COMMIT_TYPE_CHORE', "chore 📦"),
    'REVERT': get_env('GIT_ACP_COMMIT_TYPE_REVERT', "revert ⏪")
}

# Patterns for classifying commits based on file changes and commit messages
COMMIT_TYPE_PATTERNS: Final[Dict[str, List[str]]] = {
    'docs': [
        'docs/',
        '.md',
        'readme',
        'documentation',
        'license'
    ],
    'test': [
        'test',
        '.test.',
        '_test',
        'test_'
    ],
    'style': [
        'style',
        'format',
        'whitespace',
        'lint',
        'prettier',
        'eslint'
    ],
    'refactor': [
        'refactor',
        'restructure',
        'cleanup',
        'clean up',
        'reorganize'
    ],
    'fix': [
        'fix',
        'bug',
        'patch',
        'issue',
        'error',
        'crash',
        'problem',
        'resolve'
    ],
    'feat': [
        'add',
        'new',
        'feature',
        'update',
        'introduce',
        'implement',
        'enhance',
        'create',
        'improve',
        'support'
    ]
}

# Formatting Configuration
# Color settings for terminal output using rich library
COLORS: Final[Dict[str, str]] = {
    'debug_header': get_env('GIT_ACP_DEBUG_HEADER_COLOR', 'blue'),
    'debug_value': get_env('GIT_ACP_DEBUG_VALUE_COLOR', 'cyan'),
    'success': get_env('GIT_ACP_SUCCESS_COLOR', 'green'),
    'warning': get_env('GIT_ACP_WARNING_COLOR', 'yellow'),
    'status': get_env('GIT_ACP_STATUS_COLOR', 'bold green'),
    'error': get_env('GIT_ACP_ERROR_COLOR', 'bold red'),
    # AI message formatting
    'ai_message_header': get_env('GIT_ACP_AI_MESSAGE_HEADER_COLOR', 'bold yellow'),
    'ai_message_border': get_env('GIT_ACP_AI_MESSAGE_BORDER_COLOR', 'yellow'),
    'key_combination': get_env('GIT_ACP_KEY_COMBINATION_COLOR', 'cyan'),
    'instruction_text': get_env('GIT_ACP_INSTRUCTION_TEXT_COLOR', 'dim'),
    # Text style formatting
    'bold': get_env('GIT_ACP_BOLD_COLOR', 'dim')
}

# Questionary style configuration
QUESTIONARY_STYLE: Final[list[tuple[str, str]]] = [
    ('qmark', 'fg:yellow bold'),
    ('question', 'bold'),
    ('pointer', 'fg:yellow bold'),
    ('highlighted', 'fg:yellow bold'),
    ('selected', 'fg:green')
]

# Terminal Configuration
TERMINAL_WIDTH: Final[int] = get_env('GIT_ACP_TERMINAL_WIDTH', 100, int)  # Maximum width for formatted output 