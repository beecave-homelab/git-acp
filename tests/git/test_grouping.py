"""Tests for git_acp.git.classification.group_changed_files."""

from __future__ import annotations

import pytest

from git_acp.git.classification import group_changed_files


class TestGroupChangedFiles:
    """Tests for deterministic file grouping."""

    def test_empty_input_returns_empty_list(self) -> None:
        """Return an empty list when no files are provided."""
        assert group_changed_files(set()) == []

    def test_commit_type_priority_ordering(self) -> None:
        """Group commit-types first and respect priority ordering."""
        files = {
            "tests/test_core.py",
            "docs/intro.md",
            "pyproject.toml",
            "ruff.toml",
        }

        groups = group_changed_files(files)

        assert groups == [
            ["docs/intro.md"],
            ["tests/test_core.py"],
            ["ruff.toml"],
            ["pyproject.toml"],
        ]

    def test_files_sorted_within_each_group(self) -> None:
        """Sort files alphabetically within each group."""
        files = {
            "docs/b.md",
            "docs/a.md",
        }

        assert group_changed_files(files) == [["docs/a.md", "docs/b.md"]]

    def test_directory_fallback_for_unmatched_files(self) -> None:
        """Group unmatched files by a stable directory prefix."""
        files = {
            "src/core/a.py",
            "src/core/b.py",
            "src/core/c.py",
            "src/utils/x.py",
        }

        groups = group_changed_files(files)

        assert groups[0] == [
            "src/core/a.py",
            "src/core/b.py",
            "src/core/c.py",
        ]
        assert "src/utils/x.py" in groups[-1]

    def test_small_directory_groups_are_kept(self) -> None:
        """Keep small directory buckets instead of regrouping by extension."""
        files = {
            "src/a.py",
            "misc/notes.txt",
        }

        groups = group_changed_files(files)

        assert groups == [["misc/notes.txt"], ["src/a.py"]]

    def test_extension_groups_apply_to_root_level_files_only(self) -> None:
        """Group unmatched root-level files by extension."""
        files = {
            "a.py",
            "b.py",
            "notes.txt",
        }

        groups = group_changed_files(files)

        assert groups == [["a.py", "b.py"], ["notes.txt"]]

    def test_excluded_patterns_are_filtered(self) -> None:
        """Filter out excluded paths like __pycache__ and exact .env."""
        files = {
            "src/module.py",
            "__pycache__/module.cpython-312.pyc",
            ".env",
        }

        assert group_changed_files(files) == [["src/module.py"]]

    def test_group_order_commit_types_then_directories_then_extensions(self) -> None:
        """Order commit-type groups first, then directory, then extension groups."""
        files = {
            "docs/guide.md",
            "pkg/feature/a.py",
            "pkg/feature/b.py",
            "pkg/feature/c.py",
            "top_level.py",
        }

        groups = group_changed_files(files)

        assert groups[0] == ["docs/guide.md"]
        assert groups[1] == [
            "pkg/feature/a.py",
            "pkg/feature/b.py",
            "pkg/feature/c.py",
        ]
        assert groups[2] == ["top_level.py"]


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        ({"single.py"}, [["single.py"]]),
        ({"dir/file.py"}, [["dir/file.py"]]),
    ],
)
def test_edge_cases(files: set[str], expected: list[list[str]]) -> None:
    """Handle simple edge cases deterministically."""
    assert group_changed_files(files) == expected


def test_max_non_type_groups_merges_directory_groups_deterministically() -> None:
    """Merge non-type groups when a maximum is specified."""
    files = {
        "src/core/a.py",
        "src/utils/x.py",
        "src/cli/main.py",
        "src/cli/help.py",
    }

    groups = group_changed_files(files, max_non_type_groups=2)

    assert len(groups) == 2
    assert sorted([path for group in groups for path in group]) == sorted(files)
