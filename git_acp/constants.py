"""Constants module for git-acp package configuration."""

from typing import Dict, List

# AI Configuration
DEFAULT_AI_MODEL = "mevatron/diffsense:1.5b"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_BASE_URL = "http://localhost:11434/v1"  # Default Ollama API endpoint
DEFAULT_API_KEY = "ollama"  # Default API key for Ollama

# Git Configuration
DEFAULT_BRANCH = "main"
DEFAULT_REMOTE = "origin"
DEFAULT_NUM_RECENT_COMMITS = 5
DEFAULT_NUM_RELATED_COMMITS = 3
MAX_DIFF_PREVIEW_LINES = 10

# File patterns to exclude from git operations
EXCLUDED_PATTERNS = [
    '__pycache__',
    '.pyc',
    '.pyo',
    '.pyd',
    '.env',
    '.venv',
    'node_modules'
]

# Commit Type Configuration
COMMIT_TYPE_PATTERNS: Dict[str, List[str]] = {
    'docs': ['docs/', '.md', 'readme', 'documentation', 'license'],
    'test': ['test', '.test.', '_test', 'test_'],
    'style': ['style', 'format', 'whitespace', 'lint', 'prettier', 'eslint'],
    'refactor': ['refactor', 'restructure', 'cleanup', 'clean up', 'reorganize'],
    'fix': ['fix', 'bug', 'patch', 'issue', 'error', 'crash', 'problem', 'resolve'],
    'feat': ['add', 'new', 'feature', 'update', 'introduce', 'implement', 'enhance', 'create', 'improve', 'support']
}

# Formatting Configuration
COLORS = {
    'debug_header': 'blue',
    'debug_value': 'cyan',
    'success': 'green',
    'warning': 'yellow',
    'status': 'bold green',
    'error': 'bold red'
}

# Terminal Configuration
TERMINAL_WIDTH = 100 