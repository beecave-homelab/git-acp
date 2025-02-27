"""Configuration management for git-acp."""

from git_acp.config.constants import (
    COLORS,
    QUESTIONARY_STYLE,
    COMMIT_TYPES,
    COMMIT_TYPE_PATTERNS,
    EXCLUDED_PATTERNS,
    DEFAULT_REMOTE,
    DEFAULT_NUM_RECENT_COMMITS,
    DEFAULT_NUM_RELATED_COMMITS,
    DEFAULT_AI_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_BASE_URL,
    DEFAULT_API_KEY,
    DEFAULT_PROMPT_TYPE,
    DEFAULT_AI_TIMEOUT,
    TERMINAL_WIDTH
)
from git_acp.config.env_config import (
    get_env,
    load_env_config
)

__all__ = [
    'COLORS',
    'QUESTIONARY_STYLE',
    'COMMIT_TYPES',
    'COMMIT_TYPE_PATTERNS',
    'EXCLUDED_PATTERNS',
    'DEFAULT_REMOTE',
    'DEFAULT_NUM_RECENT_COMMITS',
    'DEFAULT_NUM_RELATED_COMMITS',
    'DEFAULT_AI_MODEL',
    'DEFAULT_TEMPERATURE',
    'DEFAULT_BASE_URL',
    'DEFAULT_API_KEY',
    'DEFAULT_PROMPT_TYPE',
    'DEFAULT_AI_TIMEOUT',
    'TERMINAL_WIDTH',
    'get_env',
    'load_env_config'
] 