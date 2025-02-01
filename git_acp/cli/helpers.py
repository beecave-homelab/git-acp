"""CLI helper functions."""
from rich import print as rprint
from git_acp.config.settings import TERMINAL_SETTINGS

def debug_print(config, message: str) -> None:
    """Print debug messages if verbose mode is enabled."""
    if config.verbose:
        rprint(f"[{TERMINAL_SETTINGS['colors']['warning']}]Debug: {message}[/{TERMINAL_SETTINGS['colors']['warning']}]") 