"""Environment configuration module for git-acp package.

This module handles loading environment variables from the config file
and provides fallback values from constants.
"""

import os
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path.home() / ".config" / "git-acp"


def ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)


def load_env_config() -> Optional[str]:
    """Load environment variables from the config file.

    Returns:
        Optional[str]: Error message if .env file not found, None otherwise
    """
    config_dir = get_config_dir()
    env_file = config_dir / ".env"

    if env_file.exists():
        load_dotenv(env_file)
        return None
    return "No .env file found in config directory"


def get_env(key: str, default: Any = None, type_cast: Optional[type] = None) -> Any:
    """
    Get an environment variable with optional type casting.

    Args:
        key: The environment variable key
        default: Default value if not found
        type_cast: Optional type to cast the value to

    Returns:
        The environment variable value or default
    """
    value = os.getenv(key, default)

    try:
        if type_cast == bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)

        if key == "GIT_ACP_AI_TIMEOUT" and type_cast == float:
            return _handle_timeout(value, default)

        return type_cast(value) if type_cast else value
    except (ValueError, TypeError):
        return default


def _handle_timeout(value: Any, default: Any) -> float:
    """Handle timeout value validation with error messages.

    Args:
        value: The timeout value to validate
        default: Default value to use if validation fails

    Returns:
        float: The validated timeout value
    """
    try:
        timeout = float(value)
        if timeout < 10.0:
            return 10.0
        if timeout > 300.0:
            return 300.0
        return timeout
    except (ValueError, TypeError):
        return default
