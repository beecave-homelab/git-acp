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


def load_env_config() -> None:
    """Load environment variables from the config file."""
    config_dir = get_config_dir()
    env_file = config_dir / ".env"

    # Load from config dir if exists, otherwise use default values
    if env_file.exists():
        load_dotenv(env_file)


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

    if value is not None and type_cast is not None:
        try:
            if type_cast == bool:
                # Handle boolean values
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)
            
            # Special handling for timeout values
            if key == "GIT_ACP_AI_TIMEOUT" and type_cast == float:
                timeout = float(value)
                if timeout < 10.0:
                    print(f"Warning: AI timeout {timeout}s is very low. Using minimum of 10s.")
                    return 10.0
                if timeout > 300.0:
                    print(f"Warning: AI timeout {timeout}s is very high. Using maximum of 300s.")
                    return 300.0
                return timeout
            
            return type_cast(value)
        except (ValueError, TypeError) as e:
            print(f"Warning: Failed to cast {key}={value} to {type_cast.__name__}: {str(e)}")
            return default

    return value
