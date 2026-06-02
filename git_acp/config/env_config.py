"""Environment configuration module for git-acp package.

This module handles loading environment variables from the config file
and provides fallback values from constants.
"""

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def get_config_dir() -> Path:
    """Get the configuration directory path.

    Returns:
        Path: The path to the configuration directory.
    """
    return Path.home() / ".config" / "git-acp"


def ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)


def load_env_config() -> None:
    """Load environment variables from the config file."""
    if os.getenv("GIT_ACP_ALLOW_TEST_ENV_LOAD") == "1":
        pass
    # Tests must be hermetic; do not read user-local configuration files.
    elif os.getenv("PYTEST_CURRENT_TEST") is not None or "pytest" in sys.modules:
        return

    config_dir = get_config_dir()
    env_file = config_dir / ".env"

    # Load from config dir if exists, otherwise use default values
    if env_file.exists():
        load_dotenv(env_file)


def get_env(key: str, default: Any = None, type_cast: type | None = None) -> Any:
    """Get an environment variable with optional type casting.

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
            if type_cast is bool:
                return str(value).lower() in ("true", "1", "yes", "y")
            return type_cast(value)
        except (ValueError, TypeError):
            return default

    return value


def run_setup(*, force: bool = False) -> int:
    """Run initial config setup by copying .env.example to user config dir.

    Uses importlib.resources to locate the bundled .env.example from the
    installed package, making it work regardless of installation method
    (pipx, pip, pdm, etc.).

    Args:
        force: If True, overwrite existing config file without prompting.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    import importlib.resources as pkg_resources

    config_dir = get_config_dir()
    env_file = config_dir / ".env"

    # Locate the bundled .env.example
    try:
        # Python 3.10+: as_file + files
        ref = pkg_resources.files("git_acp") / ".env.example"
        with pkg_resources.as_file(ref) as example_path:
            if not example_path.exists():
                print("❌ ERROR: .env.example not found in package installation.")
                return 1
            source_content = example_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ ERROR: Could not locate .env.example in package: {e}")
        return 1

    # Check if user config already exists
    if env_file.exists() and not force:
        print(f"⚠️  Configuration file already exists at: {env_file}")
        print("   Use --setup --force to overwrite, or edit the file directly.")
        return 0

    # Create config dir and write file
    try:
        ensure_config_dir()
        env_file.write_text(source_content, encoding="utf-8")
        print(f"✅ Configuration file created at: {env_file}")
        print("\nEdit this file to customize your settings:")
        print("  - GIT_ACP_BASE_URL (OpenAI-compatible endpoint)")
        print("  - GIT_ACP_API_KEY (API key, if required)")
        print("  - GIT_ACP_AI_MODEL (model name)")
        return 0
    except OSError as e:
        print(f"❌ ERROR: Failed to write configuration: {e}")
        return 1
