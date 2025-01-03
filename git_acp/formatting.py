"""Formatting utilities for git-acp package."""

import json
from rich import print as rprint
from rich.console import Console
from git_acp.constants import COLORS, TERMINAL_WIDTH

console = Console(width=TERMINAL_WIDTH)

def debug_header(message: str) -> None:
    """Print a debug header message."""
    rprint(f"[{COLORS['debug_header']}]Debug - {message}[/{COLORS['debug_header']}]")

def debug_item(label: str, value: str = None) -> None:
    """Print a debug item with optional value."""
    if value is not None:
        rprint(f"[{COLORS['debug_header']}]  • {label}:[/{COLORS['debug_header']}] "
               f"[{COLORS['debug_value']}]{value}[/{COLORS['debug_value']}]")
    else:
        rprint(f"[{COLORS['debug_header']}]  • {label}[/{COLORS['debug_header']}]")

def debug_json(data: dict, indent: int = 4) -> None:
    """Print formatted JSON data in debug colors."""
    json_data = json.dumps(data, indent=indent).replace('\\n', '\\n    ')
    formatted = f"[{COLORS['debug_value']}]{json_data}[{COLORS['debug_value']}]"
    rprint(formatted)

def debug_preview(text: str, num_lines: int = 10) -> None:
    """Print a preview of text content."""
    preview = text.split('\n')[:num_lines]
    rprint(f"[{COLORS['debug_value']}]" + '\n'.join(preview) + f"\n...[{COLORS['debug_value']}]")

def success(message: str) -> None:
    """Print a success message."""
    rprint(f"[{COLORS['success']}]✓[{COLORS['success']}] {message}")

def warning(message: str) -> None:
    """Print a warning message."""
    rprint(f"[{COLORS['warning']}]Warning: {message}[{COLORS['warning']}]")

def status(message: str) -> Console.status:
    """Create a status context with the given message."""
    return console.status(f"[{COLORS['status']}]{message}")
