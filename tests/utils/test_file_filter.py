"""Tests for file filtering utilities."""

from __future__ import annotations

from git_acp.utils.file_filter import filter_files_by_scope


class TestFilterFilesByScope:
    """Tests for filter_files_by_scope function."""

    def test_returns_all_files_when_add_patterns_is_none(self) -> None:
        """Return all files when add_patterns is None."""
        files = {"a.py", "b.txt", "dir/c.md"}
        result = filter_files_by_scope(files, None)
        assert result == files

    def test_returns_all_files_for_dot_pattern(self) -> None:
        """Return all files when pattern is '.' or './'."""
        files = {"a.py", "b.txt", "dir/c.md"}
        assert filter_files_by_scope(files, ".") == files
        assert filter_files_by_scope(files, "./") == files

    def test_returns_all_files_for_dot_token_among_patterns(self) -> None:
        """Return all files when '.' is included among patterns."""
        files = {"a.py", "b.txt", "dir/c.md"}
        assert filter_files_by_scope(files, "a.py .") == files
        assert filter_files_by_scope(files, "./ b.txt") == files

    def test_filters_by_exact_path(self) -> None:
        """Filter files by exact path match."""
        files = {"a.py", "b.txt", "dir/c.md"}
        result = filter_files_by_scope(files, "a.py")
        assert result == {"a.py"}

    def test_filters_by_directory_prefix(self) -> None:
        """Filter files by directory prefix."""
        files = {"a.py", "dir/b.txt", "dir/c.md", "other/d.txt"}
        result = filter_files_by_scope(files, "dir/")
        assert result == {"dir/b.txt", "dir/c.md"}

    def test_filters_by_directory_without_trailing_slash(self) -> None:
        """Filter files by directory name without trailing slash."""
        files = {"a.py", "dir/b.txt", "dir/c.md", "other/d.txt"}
        result = filter_files_by_scope(files, "dir")
        assert result == {"dir/b.txt", "dir/c.md"}

    def test_filters_by_exact_path_with_dot_slash_prefix(self) -> None:
        """Filter files by exact path when target starts with './'."""
        files = {"a.py", "b.txt", "dir/c.md"}
        result = filter_files_by_scope(files, "./a.py")
        assert result == {"a.py"}

    def test_filters_by_directory_with_dot_slash_prefix(self) -> None:
        """Filter files by directory prefix when target starts with './'."""
        files = {"a.py", "dir/b.txt", "dir/c.md", "other/d.txt"}
        result = filter_files_by_scope(files, "./dir/")
        assert result == {"dir/b.txt", "dir/c.md"}

    def test_filters_by_wildcard_pattern(self) -> None:
        """Filter files using wildcard patterns."""
        files = {"a.py", "b.txt", "c.md", "dir/d.py", "dir/e.txt"}
        result = filter_files_by_scope(files, "*.txt")
        assert result == {"b.txt", "dir/e.txt"}

    def test_filters_by_wildcard_pattern_with_directory(self) -> None:
        """Filter files using wildcard patterns with directory."""
        files = {"a.py", "dir/b.txt", "dir/c.md", "other/d.txt"}
        result = filter_files_by_scope(files, "dir/*.txt")
        assert result == {"dir/b.txt"}

    def test_filters_by_wildcard_pattern_with_dot_slash_prefix(self) -> None:
        """Filter files using wildcard patterns when target starts with './'."""
        files = {"a.py", "dir/b.txt", "dir/c.md", "other/d.txt"}
        result = filter_files_by_scope(files, "./dir/*.txt")
        assert result == {"dir/b.txt"}

    def test_filters_by_multiple_wildcard_patterns(self) -> None:
        """Filter files using multiple wildcard patterns."""
        files = {"a.py", "b.txt", "c.md", "dir/d.py", "dir/e.txt", "dir/f.md"}
        result = filter_files_by_scope(files, "*.txt *.md")
        assert result == {"b.txt", "c.md", "dir/e.txt", "dir/f.md"}

    def test_filters_by_question_mark_pattern(self) -> None:
        """Filter files using question mark wildcard."""
        files = {"a.py", "ab.py", "abc.py", "dir/d.py"}
        result = filter_files_by_scope(files, "?.py")
        assert result == {"a.py"}

    def test_filters_by_character_class_pattern(self) -> None:
        """Filter files using character class pattern."""
        files = {"a.py", "b.py", "c.py", "d.txt"}
        result = filter_files_by_scope(files, "[abc].py")
        assert result == {"a.py", "b.py", "c.py"}

    def test_combines_exact_path_and_wildcard(self) -> None:
        """Combine exact path and wildcard patterns."""
        files = {"a.py", "b.txt", "c.md", "dir/d.py", "dir/e.txt"}
        result = filter_files_by_scope(files, "a.py *.txt")
        assert result == {"a.py", "b.txt", "dir/e.txt"}

    def test_returns_empty_set_for_empty_patterns(self) -> None:
        """Return empty set when patterns result in no matches."""
        files = {"a.py", "b.txt", "c.md"}
        result = filter_files_by_scope(files, "nonexistent.py")
        assert result == set()

    def test_handles_multiple_spaces_in_patterns(self) -> None:
        """Handle multiple spaces between patterns."""
        files = {"a.py", "b.txt", "c.md"}
        result = filter_files_by_scope(files, "a.py  *.txt")
        assert result == {"a.py", "b.txt"}

    def test_handles_quoted_patterns(self) -> None:
        """Handle quoted patterns with spaces."""
        files = {"a.py", "b.txt", "c.md"}
        result = filter_files_by_scope(files, '"*.txt"')
        assert result == {"b.txt"}

    def test_wildcard_matches_subdirectories(self) -> None:
        """Ensure wildcard patterns match files in subdirectories."""
        files = {"a.txt", "dir/b.txt", "dir/sub/c.txt", "other/d.py"}
        result = filter_files_by_scope(files, "*.txt")
        assert result == {"a.txt", "dir/b.txt", "dir/sub/c.txt"}
