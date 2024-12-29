"""Formatting utilities for git-acp package."""

import json
from rich import print as rprint
from rich.console import Console

# Color constants for easy customization
DEBUG_HEADER_COLOR = "blue"
DEBUG_VALUE_COLOR = "cyan"
SUCCESS_COLOR = "green"
WARNING_COLOR = "yellow"
STATUS_COLOR = "bold green"

console = Console()

def debug_header(message: str) -> None:
    """Print a debug header message."""
    rprint(f"[{DEBUG_HEADER_COLOR}]Debug - {message}[{DEBUG_HEADER_COLOR}]")

def debug_item(label: str, value: str = None) -> None:
    """Print a debug item with optional value."""
    if value is not None:
        rprint(f"[{DEBUG_HEADER_COLOR}]  • {label}:[{DEBUG_HEADER_COLOR}] [{DEBUG_VALUE_COLOR}]{value}[{DEBUG_VALUE_COLOR}]")
    else:
        rprint(f"[{DEBUG_HEADER_COLOR}]  • {label}[{DEBUG_HEADER_COLOR}]")

def debug_json(data: dict, indent: int = 4) -> None:
    """Print formatted JSON data in debug colors."""
    formatted = f"[{DEBUG_VALUE_COLOR}]{json.dumps(data, indent=indent).replace('\\n', '\\n    ')}[{DEBUG_VALUE_COLOR}]"
    rprint(formatted)

def debug_preview(text: str, num_lines: int = 10) -> None:
    """Print a preview of text content."""
    preview = text.split('\n')[:num_lines]
    rprint(f"[{DEBUG_VALUE_COLOR}]" + '\n'.join(preview) + f"\n...[{DEBUG_VALUE_COLOR}]")

def success(message: str) -> None:
    """Print a success message."""
    rprint(f"[{SUCCESS_COLOR}]✓[{SUCCESS_COLOR}] {message}")

def warning(message: str) -> None:
    """Print a warning message."""
    rprint(f"[{WARNING_COLOR}]Warning: {message}[{WARNING_COLOR}]")

def status(message: str) -> Console.status:
    """Create a status context with the given message."""
    return console.status(f"[{STATUS_COLOR}]{message}") 