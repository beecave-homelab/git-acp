"""Git Add-Commit-Push automation package.

A command-line tool for automating Git operations with enhanced features:
- Interactive file selection
- AI-powered commit message generation
- Smart commit type classification
- Conventional commits support
"""

from git_acp.cli import main  # Re-export the main CLI entry point

__version__ = "0.15.0"

__all__ = [
    "__version__",
    "main",
]
