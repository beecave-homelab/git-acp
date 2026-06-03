#!/usr/bin/env python
"""User configuration setup script for git-acp.

Thin wrapper around the shared run_setup() function.
Can be run directly or via PDM: pdm run setup-config
"""

import sys


def main() -> None:
    """Run setup via the shared config module."""
    try:
        from git_acp.config.env_config import run_setup

        sys.exit(run_setup(force=False))
    except ImportError as e:
        print(f"❌ Error: Failed to import git_acp: {e}")
        print("Please ensure git-acp is installed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
