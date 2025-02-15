"""Terminal output formatting utilities.

This module provides functions for formatting and displaying output in the terminal,
including debug information, success messages, warnings, and status updates.
"""

import json
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from git_acp.config import COLORS, TERMINAL_WIDTH

console = Console(width=TERMINAL_WIDTH)


def debug_print(config, message: str) -> None:
    """Print debug messages if verbose mode is enabled.

    Args:
        config: Configuration object containing verbose setting
        message: The debug message to display
    """
    if config.verbose:
        warning_color = COLORS["warning"]
        rprint(f"[{warning_color}]Debug: {message}[/{warning_color}]")


def debug_header(message: str) -> None:
    """Print a debug header message with appropriate styling.

    Args:
        message: The debug header message to display
    """
    header_color = COLORS["debug_header"]
    rprint(f"[{header_color}]Debug - {message}[/{header_color}]")


def debug_item(config, label: str, value: Optional[str] = None) -> None:
    """Print a debug item with an optional value only if verbose is enabled."""
    if not config.verbose:
        return

    header_color = COLORS["debug_header"]
    value_color = COLORS["debug_value"]

    if value is not None:
        output = (
            f"[{header_color}]  • {label}:[/{header_color}] "
            f"[{value_color}]{value}[/{value_color}]"
        )
        rprint(output)
    else:
        rprint(f"[{header_color}]  • {label}[/{header_color}]")


def debug_json(data: dict, indent: int = 4) -> None:
    """Print formatted JSON data with debug styling.

    Args:
        data: The dictionary to format as JSON
        indent: Number of spaces to use for indentation
    """
    value_color = COLORS["debug_value"]
    # Convert to JSON and escape newlines
    json_data = json.dumps(data, indent=indent).replace("\\n", "\\n    ")
    # Escape Rich markup characters
    json_data = json_data.replace("[", "\\[").replace("]", "\\]")
    formatted = f"[{value_color}]{json_data}[/{value_color}]"
    rprint(formatted)


def debug_preview(text: str, num_lines: int = 10) -> None:
    """Print a preview of text content with line limit.

    Args:
        text: The text content to preview
        num_lines: Maximum number of lines to display
    """
    value_color = COLORS["debug_value"]
    preview = text.split("\n")[:num_lines]
    preview_text = "\n".join(preview) + "\n..."
    rprint(f"[{value_color}]{preview_text}[/{value_color}]")


def success(message: str) -> None:
    """Print a success message with checkmark.

    Args:
        message: The success message to display
    """
    success_color = COLORS["success"]
    rprint(f"[{success_color}]✓[/{success_color}] {message}")


def warning(message: str) -> None:
    """Print a warning message with appropriate styling.

    Args:
        message: The warning message to display
    """
    warn_color = COLORS["warning"]
    rprint(f"[{warn_color}]Warning: {message}[/{warn_color}]")


def status(message: str) -> Console.status:
    """Create a status context with styled message.

    Args:
        message: The status message to display

    Returns:
        Console.status: A status context manager for use in with statements
    """
    status_color = COLORS["status"]
    return console.status(f"[{status_color}]{message}")


def ai_message(message: str) -> None:
    """Print AI-related messages with consistent formatting."""
    ai_color = COLORS["ai_message_header"]
    rprint(f"[{ai_color}]{message}[/{ai_color}]")


def ai_border_message(
    message: str,
    title: Optional[str] = None,
    message_style: Optional[str] = "bold",
) -> None:
    """Format messages with AI border styling using Rich panels.

    Args:
        message: The message to display
        title: Optional custom title. If None, defaults to "AI Message"
        message_style: Style to apply to the message. If None, no styling is applied
    """
    border_style = COLORS["ai_message_border"]

    # Apply message styling only if provided and not None
    styled_message = (
        f"[{message_style}]{message}[/{message_style}]" if message_style else message
    )

    rprint(
        Panel(
            styled_message,
            title=title,
            border_style=border_style,
            # Ensure panel expands to full width
            expand=True,
        )
    )


def key_combination(message: str) -> None:
    """Format keyboard combinations with consistent styling."""
    key_color = COLORS["key_combination"]
    rprint(f"[{key_color}]{message}[/{key_color}]")


def instruction_text(message: str) -> None:
    """Display instructional text with muted formatting."""
    instr_color = COLORS["instruction_text"]
    rprint(f"[{instr_color}]{message}[/{instr_color}]")


def bold_text(message: str) -> None:
    """Emphasize text with bold formatting."""
    bold_color = COLORS["bold"]
    rprint(f"[{bold_color}]{message}[/{bold_color}]")


class ProgressReporter:
    """Handle non-verbose progress reporting.

    A class to manage progress reporting in non-verbose mode, providing methods to
    start, end and update progress stages.

    Attributes:
        verbose (bool): Flag to control verbose output mode
        current_status: Current status context manager for progress reporting
    """

    def __init__(self, verbose: bool = False):
        """Initialize the ProgressReporter.

        Args:
            verbose (bool, optional): Flag to control verbose output. Defaults to False.
        """
        self.verbose = verbose
        self.current_status = None

    def start_stage(self, message: str) -> None:
        """Start a new progress reporting stage.

        Args:
            message (str): The message to display for this stage
        """
        if not self.verbose:
            # End any existing stage before starting a new one
            if self.current_status is not None:
                self.current_status.__exit__(None, None, None)
                self.current_status = None
            
            self.current_status = console.status(f"[{COLORS['status']}]{message}")
            self.current_status.__enter__()

    def end_stage(self, message: str) -> None:
        """End the current progress reporting stage.

        Args:
            message (str): Success message to display when ending the stage
        """
        if not self.verbose and self.current_status:
            self.current_status.__exit__(None, None, None)
            self.current_status = None
            success(message)

    def update(self, message: str) -> None:
        """Update the current progress stage with a new message.

        Args:
            message (str): The new message to display
        """
        if not self.verbose:
            instruction_text(message)
