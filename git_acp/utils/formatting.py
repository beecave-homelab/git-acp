"""Terminal output formatting utilities.

This module provides functions for formatting and displaying output in the terminal,
including debug information, success messages, warnings, and status updates.
"""

import json

from rich import print as rprint
from rich.console import Console
from rich.markup import escape

from git_acp.config import COLORS, MAX_DEBUG_VALUE_CHARS, TERMINAL_WIDTH

console = Console(width=TERMINAL_WIDTH)


def debug_header(message: str) -> None:
    """Print a debug header message with appropriate styling.

    Args:
        message: The debug header message to display
    """
    rprint(f"[{COLORS['debug_header']}]Debug - {message}[/{COLORS['debug_header']}]")


def debug_item(label: str, value: str = None) -> None:
    """Print a debug item with an optional value.

    Values longer than the configured maximum are truncated with a notice.
    Rich markup in values is automatically escaped for safe rendering.

    Args:
        label: The label for the debug item
        value: Optional value to display after the label
    """
    if value is not None:
        total_len = len(value)
        if total_len > MAX_DEBUG_VALUE_CHARS:
            value = (
                f"{value[:MAX_DEBUG_VALUE_CHARS]}\n"
                f"... [truncated {total_len - MAX_DEBUG_VALUE_CHARS} chars; "
                f"total {total_len}]"
            )
        safe_value = escape(value)
        rprint(
            f"[{COLORS['debug_header']}]  • {label}:[/{COLORS['debug_header']}] "
            f"[{COLORS['debug_value']}]{safe_value}[/{COLORS['debug_value']}]"
        )
    else:
        rprint(f"[{COLORS['debug_header']}]  • {label}[/{COLORS['debug_header']}]")


def debug_json(data: dict, indent: int = 4) -> None:
    """Print formatted JSON data with debug styling.

    Args:
        data: The dictionary to format as JSON
        indent: Number of spaces to use for indentation
    """
    json_data = json.dumps(data, indent=indent).replace("\\n", "\\n    ")
    formatted = f"[{COLORS['debug_value']}]{json_data}[{COLORS['debug_value']}]"
    rprint(formatted)


def debug_preview(text: str, num_lines: int = 10) -> None:
    """Print a preview of text content with line limit.

    Args:
        text: The text content to preview
        num_lines: Maximum number of lines to display
    """
    preview = text.split("\n")[:num_lines]
    rprint(
        f"[{COLORS['debug_value']}]"
        + "\n".join(preview)
        + f"\n...[{COLORS['debug_value']}]"
    )


def success(message: str) -> None:
    """Print a success message with checkmark.

    Args:
        message: The success message to display
    """
    rprint(f"[{COLORS['success']}]✓[{COLORS['success']}] {message}")


def warning(message: str) -> None:
    """Print a warning message with appropriate styling.

    Args:
        message: The warning message to display
    """
    rprint(f"[{COLORS['warning']}]Warning: {message}[{COLORS['warning']}]")


def status(message: str) -> Console.status:
    """Create a status context with styled message.

    Args:
        message: The status message to display

    Returns:
        Console.status: A status context manager for use in with statements
    """
    return console.status(f"[{COLORS['status']}]{message}")
