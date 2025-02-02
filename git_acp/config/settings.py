"""Grouped settings for git_acp package."""
from git_acp.config.env_config import get_env
from git_acp.config.constants import (
    DEFAULT_AI_MODEL,
    DEFAULT_PR_AI_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_BASE_URL,
    DEFAULT_API_KEY,
    DEFAULT_PROMPT_TYPE,
    DEFAULT_AI_TIMEOUT,
    DEFAULT_BRANCH,
    DEFAULT_REMOTE,
    DEFAULT_NUM_RECENT_COMMITS,
    DEFAULT_NUM_RELATED_COMMITS,
    MAX_DIFF_PREVIEW_LINES,
    EXCLUDED_PATTERNS,
    COMMIT_TYPES,
    COMMIT_TYPE_PATTERNS,
    COLORS,
    QUESTIONARY_STYLE,
    TERMINAL_WIDTH
)

AI_SETTINGS = {
    "model": DEFAULT_AI_MODEL,
    "pr_model": DEFAULT_PR_AI_MODEL,
    "temperature": DEFAULT_TEMPERATURE,
    "base_url": DEFAULT_BASE_URL,
    "api_key": DEFAULT_API_KEY,
    "prompt_type": DEFAULT_PROMPT_TYPE,
    "timeout": DEFAULT_AI_TIMEOUT,
}

GIT_SETTINGS = {
    "default_branch": DEFAULT_BRANCH,
    "default_remote": DEFAULT_REMOTE,
    "num_recent_commits": DEFAULT_NUM_RECENT_COMMITS,
    "num_related_commits": DEFAULT_NUM_RELATED_COMMITS,
    "max_diff_preview_lines": MAX_DIFF_PREVIEW_LINES,
    "excluded_patterns": EXCLUDED_PATTERNS,
    "commit_types": COMMIT_TYPES,
    "commit_type_patterns": COMMIT_TYPE_PATTERNS,
}

TERMINAL_SETTINGS = {
    "colors": COLORS,
    "questionary_style": QUESTIONARY_STYLE,
    "width": TERMINAL_WIDTH,
} 