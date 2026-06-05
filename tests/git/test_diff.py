"""Tests for git_acp.git.diff module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from git_acp.git.core import GitError
from git_acp.git.diff import _BINARY_LINE_COUNT, extract_added_lines, get_changed_files, get_diff, get_numstat
from git_acp.utils import GitConfig


class TestGetChangedFiles:
    """Tests for get_changed_files function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__staged_only_returns_staged_files(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return staged files when staged_only is True."""
        mock_run.return_value = ("file1.py\nfile2.py", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        mock_run.assert_called_once_with(
            ["git", "diff", "--staged", "--name-only"], mock_config
        )
        assert result == {"file1.py", "file2.py"}

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__staged_only_empty(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return empty set when no staged files exist."""
        mock_run.return_value = ("", "")

        result = get_changed_files(config=mock_config, staged_only=True)

        assert result == set()

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__status_mode_parses_porcelain(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Parse porcelain status output correctly."""
        mock_run.return_value = (
            " M modified.py\nA  added.py\n?? untracked.py\nMM both_modified.py",
            "",
        )

        result = get_changed_files(config=mock_config, staged_only=False)

        assert "modified.py" in result
        assert "added.py" in result
        assert "untracked.py" in result
        assert "both_modified.py" in result

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__handles_rename_arrow(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Handle renamed files with arrow notation."""
        mock_run.return_value = ("R  old_name.py -> new_name.py", "")

        result = get_changed_files(config=mock_config, staged_only=False)

        assert "new_name.py" in result
        assert "old_name.py" not in result

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__excludes_pycache(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Exclude __pycache__ files from results."""
        mock_run.return_value = (
            " M valid.py\n"
            " M __pycache__/module.cpython-39.pyc\n"
            " M src/__pycache__/other.pyc",
            "",
        )

        result = get_changed_files(config=mock_config, staged_only=False)

        assert "valid.py" in result
        assert "__pycache__/module.cpython-39.pyc" not in result
        assert "src/__pycache__/other.pyc" not in result

    @patch("git_acp.git.diff.run_git_command")
    def test_get_changed_files__skips_empty_lines(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Skip empty lines in status output."""
        mock_run.return_value = (
            " M file1.py\n\n   \n M file2.py",
            "",
        )

        result = get_changed_files(config=mock_config, staged_only=False)

        assert result == {"file1.py", "file2.py"}

    @patch("git_acp.git.diff.run_git_command")
    @patch("git_acp.git.diff.debug_header")
    @patch("git_acp.git.diff.debug_item")
    def test_get_changed_files__verbose_mode_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = (" M file.py", "")

        get_changed_files(config=verbose_config, staged_only=False)

        mock_debug_header.assert_called()
        mock_debug_item.assert_called()

    @patch("git_acp.git.diff.run_git_command")
    @patch("git_acp.git.diff.debug_header")
    @patch("git_acp.git.diff.debug_item")
    def test_get_changed_files__staged_verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output for staged files in verbose mode."""
        mock_run.return_value = ("staged.py", "")

        get_changed_files(config=verbose_config, staged_only=True)

        mock_debug_header.assert_called()
        mock_debug_item.assert_called()

    @patch("git_acp.git.diff.run_git_command")
    @patch("git_acp.git.diff.debug_item")
    def test_get_changed_files__verbose_logs_exclusion(
        self,
        mock_debug_item: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log file exclusion in verbose mode."""
        mock_run.return_value = (" M __pycache__/file.pyc", "")

        get_changed_files(config=verbose_config, staged_only=False)

        # Should have logged exclusion
        exclusion_logged = any(
            "Excluding" in str(call) for call in mock_debug_item.call_args_list
        )
        assert exclusion_logged

    def test_get_changed_files__no_config(self) -> None:
        """Work without a config object."""
        with patch("git_acp.git.diff.run_git_command") as mock_run:
            mock_run.return_value = (" M file.py", "")

            result = get_changed_files(config=None, staged_only=False)

            assert result == {"file.py"}


class TestGetDiff:
    """Tests for get_diff function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff__staged_returns_staged_diff(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return staged diff output."""
        mock_run.return_value = ("diff --staged output", "")

        result = get_diff(diff_type="staged", config=mock_config)

        mock_run.assert_called_once_with(["git", "diff", "--staged"], mock_config)
        assert result == "diff --staged output"

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff__unstaged_returns_unstaged_diff(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return unstaged diff output."""
        mock_run.return_value = ("diff output", "")

        result = get_diff(diff_type="unstaged", config=mock_config)

        mock_run.assert_called_once_with(["git", "diff"], mock_config)
        assert result == "diff output"

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff__default_is_staged(self, mock_run: MagicMock) -> None:
        """Default to staged diff when no type specified."""
        mock_run.return_value = ("staged diff", "")

        result = get_diff()

        mock_run.assert_called_once_with(["git", "diff", "--staged"], None)
        assert result == "staged diff"

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff__raises_git_error_on_failure(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when diff command fails."""
        mock_run.side_effect = GitError("git diff failed")

        with pytest.raises(GitError) as exc:
            get_diff(diff_type="staged", config=mock_config)

        assert "Failed to get staged diff" in str(exc.value)

    @patch("git_acp.git.diff.run_git_command")
    @patch("git_acp.git.diff.debug_header")
    @patch("git_acp.git.diff.debug_item")
    def test_get_diff__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("diff content", "")

        get_diff(diff_type="staged", config=verbose_config)

        mock_debug_header.assert_called_with("Getting staged diff")
        mock_debug_item.assert_called_with("Diff length", "12")

    @patch("git_acp.git.diff.run_git_command")
    def test_get_diff__returns_empty_string_on_no_diff(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return empty string when no diff exists."""
        mock_run.return_value = ("", "")

        result = get_diff(diff_type="staged", config=mock_config)

        assert result == ""


class TestGetNumstat:
    """Tests for get_numstat function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a non-verbose config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.diff.run_git_command")
    def test_staged_output_is_used_first(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Use staged numstat output when it is non-empty."""
        staged_output = "5\t3\tsrc/module.py\n"
        mock_run.return_value = (staged_output, "")

        result = get_numstat(mock_config)

        assert "src/module.py" in result
        assert result["src/module.py"] == (5, 3)

    @patch("git_acp.git.diff.run_git_command")
    def test_falls_back_to_unstaged_when_staged_empty(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Fall back to unstaged numstat when staged output is empty."""
        unstaged_output = "10\t2\tgit_acp/cli.py\n"
        # First call (staged) returns empty, second call (unstaged) returns data
        mock_run.side_effect = [("", ""), (unstaged_output, "")]

        result = get_numstat(mock_config)

        assert "git_acp/cli.py" in result
        assert result["git_acp/cli.py"] == (10, 2)

    @patch("git_acp.git.diff.run_git_command")
    def test_returns_empty_dict_when_no_output(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return empty dict when both staged and unstaged output are empty."""
        mock_run.return_value = ("", "")

        result = get_numstat(mock_config)

        assert result == {}

    @patch("git_acp.git.diff.run_git_command")
    def test_binary_file_receives_default_line_count(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Binary files (shown as '-') get _BINARY_LINE_COUNT added lines and 0 removed."""
        binary_output = "-\t-\timage.png\n"
        mock_run.return_value = (binary_output, "")

        result = get_numstat(mock_config)

        assert "image.png" in result
        added, removed = result["image.png"]
        assert added == _BINARY_LINE_COUNT
        assert removed == 0

    @patch("git_acp.git.diff.run_git_command")
    def test_binary_line_count_constant_is_ten(self, mock_run: MagicMock) -> None:
        """_BINARY_LINE_COUNT should equal 10."""
        assert _BINARY_LINE_COUNT == 10

    @patch("git_acp.git.diff.run_git_command")
    def test_multiple_files_parsed(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Parse multiple lines correctly."""
        output = "3\t1\tsrc/a.py\n10\t5\tsrc/b.py\n0\t2\tsrc/c.py\n"
        mock_run.return_value = (output, "")

        result = get_numstat(mock_config)

        assert result["src/a.py"] == (3, 1)
        assert result["src/b.py"] == (10, 5)
        assert result["src/c.py"] == (0, 2)

    @patch("git_acp.git.diff.run_git_command")
    def test_excludes_pycache_files(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Files in __pycache__ are excluded from results."""
        output = "5\t2\tsrc/module.py\n3\t0\t__pycache__/module.cpython-311.pyc\n"
        mock_run.return_value = (output, "")

        result = get_numstat(mock_config)

        assert "src/module.py" in result
        assert "__pycache__/module.cpython-311.pyc" not in result

    @patch("git_acp.git.diff.run_git_command")
    def test_excludes_dot_env_file(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Files named '.env' are excluded from results."""
        output = "5\t2\tsrc/module.py\n2\t1\t.env\n"
        mock_run.return_value = (output, "")

        result = get_numstat(mock_config)

        assert "src/module.py" in result
        assert ".env" not in result

    @patch("git_acp.git.diff.run_git_command")
    def test_skips_malformed_lines(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Lines not matching the expected tab-delimited format are skipped."""
        # Line with only 2 tab-separated fields (invalid)
        output = "5\tsrc/module.py\n3\t1\tsrc/valid.py\n"
        mock_run.return_value = (output, "")

        result = get_numstat(mock_config)

        assert "src/valid.py" in result
        assert "src/module.py" not in result

    @patch("git_acp.git.diff.run_git_command")
    def test_skips_blank_lines(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Blank lines in numstat output are skipped without error."""
        output = "5\t2\tsrc/a.py\n\n\n3\t1\tsrc/b.py\n"
        mock_run.return_value = (output, "")

        result = get_numstat(mock_config)

        assert "src/a.py" in result
        assert "src/b.py" in result

    @patch("git_acp.git.diff.run_git_command")
    def test_git_error_on_first_command_falls_back(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """A GitError on the staged command is caught and falls back to unstaged."""
        unstaged_output = "7\t1\tsrc/module.py\n"
        mock_run.side_effect = [GitError("no staged changes"), (unstaged_output, "")]

        result = get_numstat(mock_config)

        assert "src/module.py" in result

    @patch("git_acp.git.diff.run_git_command")
    def test_git_error_on_both_commands_returns_empty(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """GitError on both staged and unstaged returns an empty dict."""
        mock_run.side_effect = GitError("git unavailable")

        result = get_numstat(mock_config)

        assert result == {}

    @patch("git_acp.git.diff.run_git_command")
    def test_none_config_is_accepted(self, mock_run: MagicMock) -> None:
        """get_numstat works without a config object."""
        mock_run.return_value = ("4\t1\tsrc/mod.py\n", "")

        result = get_numstat(None)

        assert "src/mod.py" in result

    @patch("git_acp.git.diff.run_git_command")
    @patch("git_acp.git.diff.debug_header")
    @patch("git_acp.git.diff.debug_item")
    def test_verbose_logs_parsing_header(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Verbose mode logs parsing header and entry count."""
        mock_run.return_value = ("5\t2\tsrc/module.py\n", "")

        get_numstat(verbose_config)

        mock_debug_header.assert_any_call("Parsing numstat output")
        mock_debug_item.assert_any_call("Numstat entries", "1")


class TestExtractAddedLines:
    """Tests for extract_added_lines in diff.py."""

    def test_extracts_added_lines_only(self) -> None:
        """Return only lines starting with +, stripping the marker."""
        diff = (
            "diff --git a/file.py b/file.py\n"
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "@@ -1,3 +1,4 @@\n"
            " context line\n"
            "-removed line\n"
            "+added line one\n"
            "+added line two\n"
        )
        result = extract_added_lines(diff)
        assert "added line one" in result
        assert "added line two" in result
        assert "context line" not in result
        assert "removed line" not in result

    def test_empty_diff_returns_empty_string(self) -> None:
        """Return empty string for empty input."""
        assert extract_added_lines("") == ""

    def test_skips_file_headers(self) -> None:
        """Do not include +++ and --- lines."""
        diff = "+++ b/new_file.py\n--- a/old_file.py\n+actual change\n"
        result = extract_added_lines(diff)
        assert "b/new_file.py" not in result
        assert "a/old_file.py" not in result
        assert "actual change" in result

    def test_skips_hunk_headers(self) -> None:
        """Lines starting with @@ are excluded."""
        diff = "@@ -1,3 +1,5 @@\n+added line\n"
        result = extract_added_lines(diff)
        assert "@@ -1,3 +1,5 @@" not in result
        assert "added line" in result

    def test_no_added_lines_returns_empty(self) -> None:
        """Diff with only removed lines produces an empty string."""
        diff = "-removed line\n-another removed\n"
        result = extract_added_lines(diff)
        assert result == ""

    def test_only_context_lines_returns_empty(self) -> None:
        """Diff with only context lines (no + prefix) produces an empty string."""
        diff = " context line one\n context line two\n"
        result = extract_added_lines(diff)
        assert result == ""

    def test_leading_plus_stripped(self) -> None:
        """The leading '+' character is stripped from each added line."""
        diff = "+def new_function():\n+    pass\n"
        result = extract_added_lines(diff)
        assert result.startswith("def new_function():")
        assert "+" not in result

    def test_output_lines_joined_with_newline(self) -> None:
        """Multiple added lines are joined with newlines."""
        diff = "+line one\n+line two\n+line three\n"
        result = extract_added_lines(diff)
        lines = result.split("\n")
        assert lines == ["line one", "line two", "line three"]

    def test_empty_added_line_preserved(self) -> None:
        """An added blank line (just '+') produces an empty string entry."""
        diff = "+first line\n+\n+third line\n"
        result = extract_added_lines(diff)
        assert "first line" in result
        assert "third line" in result

    def test_triple_plus_hunk_body_excluded(self) -> None:
        """Lines starting with +++ (file header) are not extracted."""
        diff = "+++ b/file.py\n+actual addition\n"
        result = extract_added_lines(diff)
        assert "b/file.py" not in result
        assert "actual addition" in result

    def test_realistic_diff(self) -> None:
        """End-to-end test with realistic diff content."""
        diff = (
            "diff --git a/git_acp/cli.py b/git_acp/cli.py\n"
            "index abc..def 100644\n"
            "--- a/git_acp/cli.py\n"
            "+++ b/git_acp/cli.py\n"
            "@@ -10,6 +10,8 @@ def main():\n"
            " existing_code()\n"
            "-old_function()\n"
            "+new_function()\n"
            "+another_call()\n"
            " more_code()\n"
        )
        result = extract_added_lines(diff)
        assert "new_function()" in result
        assert "another_call()" in result
        assert "old_function()" not in result
        assert "existing_code()" not in result
        assert "more_code()" not in result
