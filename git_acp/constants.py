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

from typing import Dict, List, Final, Tuple

# AI Configuration
# Settings for OpenAI-compatible API interaction
DEFAULT_AI_MODEL: Final[str] = "mevatron/diffsense:1.5b"
DEFAULT_TEMPERATURE: Final[float] = 0.7
DEFAULT_BASE_URL: Final[str] = "http://192.168.2.108:11434/v1"  # Ollama API endpoint
DEFAULT_API_KEY: Final[str] = "ollama"  # Default API key for Ollama

# Git Configuration
# Basic settings for git operations
DEFAULT_BRANCH: Final[str] = "main"
DEFAULT_REMOTE: Final[str] = "origin"
DEFAULT_NUM_RECENT_COMMITS: Final[int] = 3
DEFAULT_NUM_RELATED_COMMITS: Final[int] = 3
MAX_DIFF_PREVIEW_LINES: Final[int] = 10

# File patterns to exclude from git operations
# These patterns match common build artifacts and environment-specific files
EXCLUDED_PATTERNS: Final[List[str]] = [
    '__pycache__',  # Python bytecode cache
    '.pyc',         # Compiled Python files
    '.pyo',         # Optimized Python files
    '.pyd',         # Python DLL files
    '.env',         # Environment variables file
    '.venv',        # Virtual environment directory
    'node_modules'  # Node.js dependencies
]

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
    'debug_header': 'blue',    # Debug section headers
    'debug_value': 'cyan',     # Debug values
    'success': 'green',        # Success messages
    'warning': 'yellow',       # Warning messages
    'status': 'bold green',    # Status updates
    'error': 'bold red'        # Error messages
}

# Questionary style configuration
QUESTIONARY_STYLE: Final[List[Tuple[str, str]]] = [
    ('qmark', 'fg:yellow bold'),
    ('question', 'bold'),
    ('pointer', 'fg:yellow bold'),
    ('highlighted', 'fg:yellow bold'),
    ('selected', 'fg:green')
]

# Terminal Configuration
TERMINAL_WIDTH: Final[int] = 100  # Maximum width for formatted output 