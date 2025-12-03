"""Unit tests for formatting utilities."""

from git_acp.utils import formatting


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


def test_debug_item__with_value(capsys):
    """Test debug_item with a value displays both label and value."""
    formatting.debug_item("Label", "Value")
    captured = capsys.readouterr()
    assert "Label" in captured.out
    assert "Value" in captured.out


def test_debug_item__without_value(capsys):
    """Test debug_item without a value displays only the label."""
    formatting.debug_item("OnlyLabel")
    captured = capsys.readouterr()
    assert "OnlyLabel" in captured.out


def test_debug_json__formats_dict(capsys):
    """Test debug_json formats dictionary as JSON."""
    test_data = {"key": "value", "number": 42}
    formatting.debug_json(test_data)
    captured = capsys.readouterr()
    assert "key" in captured.out
    assert "value" in captured.out
    assert "42" in captured.out


def test_debug_json__custom_indent(capsys):
    """Test debug_json respects custom indentation."""
    test_data = {"nested": {"inner": "data"}}
    formatting.debug_json(test_data, indent=2)
    captured = capsys.readouterr()
    assert "nested" in captured.out
    assert "inner" in captured.out


def test_warning__displays_message(capsys):
    """Test warning displays warning message."""
    formatting.warning("This is a warning")
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "This is a warning" in captured.out


def test_debug_header__displays_message(capsys):
    """Test debug_header displays header message."""
    formatting.debug_header("Test Header")
    captured = capsys.readouterr()
    assert "Debug" in captured.out
    assert "Test Header" in captured.out


def test_success__displays_message(capsys):
    """Test success displays success message with checkmark."""
    formatting.success("Operation completed")
    captured = capsys.readouterr()
    assert "✓" in captured.out
    assert "Operation completed" in captured.out
