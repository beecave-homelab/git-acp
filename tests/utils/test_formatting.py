"""Unit tests for formatting utilities."""

from unittest.mock import patch
import pytest
from git_acp.utils import formatting
from git_acp.config import COLORS


def test_debug_preview_truncation(capsys):
    """Test text preview truncation functionality."""
    long_text = (
        "Line1\nLine2\nLine3\nLine4\nLine5\nLine6\nLine7\nLine8\nLine9\nLine10\nLine11"
    )
    formatting.debug_preview(long_text, num_lines=5)
    captured = capsys.readouterr()
    assert "Line5" in captured.out
    assert "Line11" not in captured.out
    assert "..." in captured.out


def test_status_context_manager():
    """Test status context manager initialization."""
    with formatting.status("Processing...") as status_obj:
        assert status_obj is not None
        assert "Processing..." in status_obj.renderable.text


def test_terminal_width_enforcement():
    """Test terminal width configuration from constants."""
    assert formatting.console.width == formatting.TERMINAL_WIDTH
