"""Tests for git_acp.git.management module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from git_acp.git.core import GitError
from git_acp.git.management import (
    create_branch,
    delete_branch,
    manage_remote,
    manage_stash,
    manage_tags,
    merge_branch,
)
from git_acp.utils import GitConfig


class TestCreateBranch:
    """Tests for create_branch function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.management.run_git_command")
    def test_create_branch__creates_new_branch(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Create a new branch with checkout -b."""
        mock_run.return_value = ("", "")

        create_branch("feature-branch", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "checkout", "-b", "feature-branch"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    @patch("git_acp.git.management.debug_header")
    @patch("git_acp.git.management.debug_item")
    def test_create_branch__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("", "")

        create_branch("test-branch", config=verbose_config)

        mock_debug_header.assert_called_with("Creating branch")
        mock_debug_item.assert_called_with("Creating branch", "test-branch")

    @patch("git_acp.git.management.run_git_command")
    def test_create_branch__raises_git_error_on_failure(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when branch creation fails."""
        mock_run.side_effect = GitError("branch already exists")

        with pytest.raises(GitError) as exc:
            create_branch("existing-branch", config=mock_config)

        assert "Failed to create branch" in str(exc.value)


class TestDeleteBranch:
    """Tests for delete_branch function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.management.run_git_command")
    def test_delete_branch__deletes_branch(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Delete a branch with -d flag."""
        mock_run.return_value = ("", "")

        delete_branch("old-branch", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "branch", "-d", "old-branch"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    def test_delete_branch__force_delete(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Force delete a branch with -D flag."""
        mock_run.return_value = ("", "")

        delete_branch("unmerged-branch", force=True, config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "branch", "-D", "unmerged-branch"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    @patch("git_acp.git.management.debug_header")
    @patch("git_acp.git.management.debug_item")
    def test_delete_branch__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("", "")

        delete_branch("test-branch", config=verbose_config)

        mock_debug_header.assert_called_with("Deleting branch")
        mock_debug_item.assert_called_with("Deleting branch", "test-branch")

    @patch("git_acp.git.management.run_git_command")
    def test_delete_branch__raises_git_error_on_failure(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when branch deletion fails."""
        mock_run.side_effect = GitError("branch not found")

        with pytest.raises(GitError) as exc:
            delete_branch("nonexistent", config=mock_config)

        assert "Failed to delete branch" in str(exc.value)


class TestMergeBranch:
    """Tests for merge_branch function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.management.run_git_command")
    def test_merge_branch__merges_source_branch(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Merge a source branch into current branch."""
        mock_run.return_value = ("", "")

        merge_branch("feature-branch", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "merge", "feature-branch"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    @patch("git_acp.git.management.debug_header")
    @patch("git_acp.git.management.debug_item")
    def test_merge_branch__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_debug_header: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("", "")

        merge_branch("test-branch", config=verbose_config)

        mock_debug_header.assert_called_with("Merging branch")
        mock_debug_item.assert_called_with("Merging branch", "test-branch")

    @patch("git_acp.git.management.run_git_command")
    def test_merge_branch__raises_git_error_on_conflict(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError on merge conflict."""
        mock_run.side_effect = GitError("merge conflict")

        with pytest.raises(GitError) as exc:
            merge_branch("conflicting-branch", config=mock_config)

        assert "Failed to merge branch" in str(exc.value)


class TestManageRemote:
    """Tests for manage_remote function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.management.run_git_command")
    def test_manage_remote__add_remote(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Add a new remote."""
        mock_run.return_value = ("", "")

        manage_remote(
            "add", "upstream", "https://github.com/upstream/repo.git", mock_config
        )

        mock_run.assert_called_once_with(
            [
                "git",
                "remote",
                "add",
                "upstream",
                "https://github.com/upstream/repo.git",
            ],
            mock_config,
        )

    @patch("git_acp.git.management.run_git_command")
    def test_manage_remote__remove_remote(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Remove an existing remote."""
        mock_run.return_value = ("", "")

        manage_remote("remove", "upstream", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "remote", "remove", "upstream"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    def test_manage_remote__set_url(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Set remote URL."""
        mock_run.return_value = ("", "")

        manage_remote(
            "set-url", "origin", "https://github.com/new/repo.git", mock_config
        )

        mock_run.assert_called_once_with(
            [
                "git",
                "remote",
                "set-url",
                "origin",
                "https://github.com/new/repo.git",
            ],
            mock_config,
        )

    def test_manage_remote__add_requires_url(self) -> None:
        """Raise GitError when adding remote without URL."""
        with pytest.raises(GitError) as exc:
            manage_remote("add", "upstream", url=None)

        assert "URL is required" in str(exc.value)

    def test_manage_remote__set_url_requires_url(self) -> None:
        """Raise GitError when setting URL without URL parameter."""
        with pytest.raises(GitError) as exc:
            manage_remote("set-url", "origin", url=None)

        assert "URL is required" in str(exc.value)

    @patch("git_acp.git.management.run_git_command")
    @patch("git_acp.git.management.debug_item")
    def test_manage_remote__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("", "")

        manage_remote("add", "test", "https://test.com/repo.git", verbose_config)

        mock_debug_item.assert_called()

    @patch("git_acp.git.management.run_git_command")
    def test_manage_remote__raises_git_error_on_failure(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when remote operation fails."""
        mock_run.side_effect = GitError("remote already exists")

        with pytest.raises(GitError) as exc:
            manage_remote("add", "origin", "https://test.com", mock_config)

        assert "Failed to add remote" in str(exc.value)


class TestManageTags:
    """Tests for manage_tags function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.management.run_git_command")
    def test_manage_tags__create_lightweight_tag(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Create a lightweight tag."""
        mock_run.return_value = ("", "")

        manage_tags("create", "v1.0.0", config=mock_config)

        mock_run.assert_called_once_with(["git", "tag", "v1.0.0"], mock_config)

    @patch("git_acp.git.management.run_git_command")
    def test_manage_tags__create_annotated_tag(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Create an annotated tag with message."""
        mock_run.return_value = ("", "")

        manage_tags("create", "v1.0.0", message="Release 1.0.0", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "tag", "-a", "v1.0.0", "-m", "Release 1.0.0"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    def test_manage_tags__delete_tag(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Delete a tag."""
        mock_run.return_value = ("", "")

        manage_tags("delete", "v1.0.0", config=mock_config)

        mock_run.assert_called_once_with(["git", "tag", "-d", "v1.0.0"], mock_config)

    @patch("git_acp.git.management.run_git_command")
    def test_manage_tags__push_tag(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Push a tag to remote."""
        mock_run.return_value = ("", "")

        manage_tags("push", "v1.0.0", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "push", "origin", "v1.0.0"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    @patch("git_acp.git.management.debug_item")
    def test_manage_tags__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("", "")

        manage_tags("create", "v1.0.0", config=verbose_config)

        mock_debug_item.assert_called()

    @patch("git_acp.git.management.run_git_command")
    def test_manage_tags__raises_git_error_on_failure(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when tag operation fails."""
        mock_run.side_effect = GitError("tag already exists")

        with pytest.raises(GitError) as exc:
            manage_tags("create", "v1.0.0", config=mock_config)

        assert "Failed to create tag" in str(exc.value)


class TestManageStash:
    """Tests for manage_stash function."""

    @pytest.fixture
    def mock_config(self) -> GitConfig:
        """Return a mock config object."""
        return GitConfig(verbose=False)

    @pytest.fixture
    def verbose_config(self) -> GitConfig:
        """Return a verbose config object."""
        return GitConfig(verbose=True)

    @patch("git_acp.git.management.run_git_command")
    def test_manage_stash__save_without_message(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Save stash without a message."""
        mock_run.return_value = ("", "")

        manage_stash("save", config=mock_config)

        mock_run.assert_called_once_with(["git", "stash", "push"], mock_config)

    @patch("git_acp.git.management.run_git_command")
    def test_manage_stash__save_with_message(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Save stash with a message."""
        mock_run.return_value = ("", "")

        manage_stash("save", message="WIP: feature work", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "stash", "push", "-m", "WIP: feature work"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    def test_manage_stash__pop_default(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Pop the most recent stash."""
        mock_run.return_value = ("", "")

        manage_stash("pop", config=mock_config)

        mock_run.assert_called_once_with(["git", "stash", "pop"], mock_config)

    @patch("git_acp.git.management.run_git_command")
    def test_manage_stash__pop_specific(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Pop a specific stash."""
        mock_run.return_value = ("", "")

        manage_stash("pop", stash_id="stash@{1}", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "stash", "pop", "stash@{1}"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    def test_manage_stash__apply_default(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Apply the most recent stash."""
        mock_run.return_value = ("", "")

        manage_stash("apply", config=mock_config)

        mock_run.assert_called_once_with(["git", "stash", "apply"], mock_config)

    @patch("git_acp.git.management.run_git_command")
    def test_manage_stash__apply_specific(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Apply a specific stash."""
        mock_run.return_value = ("", "")

        manage_stash("apply", stash_id="stash@{0}", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "stash", "apply", "stash@{0}"], mock_config
        )

    @patch("git_acp.git.management.run_git_command")
    def test_manage_stash__drop_specific(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Drop a specific stash."""
        mock_run.return_value = ("", "")

        manage_stash("drop", stash_id="stash@{0}", config=mock_config)

        mock_run.assert_called_once_with(
            ["git", "stash", "drop", "stash@{0}"], mock_config
        )

    def test_manage_stash__drop_requires_stash_id(self) -> None:
        """Raise GitError when dropping stash without ID."""
        with pytest.raises(GitError) as exc:
            manage_stash("drop", stash_id=None)

        assert "Stash ID is required" in str(exc.value)

    @patch("git_acp.git.management.run_git_command")
    def test_manage_stash__list_returns_output(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """List stashes and return output."""
        mock_run.return_value = ("stash@{0}: WIP on main", "")

        result = manage_stash("list", config=mock_config)

        mock_run.assert_called_once_with(["git", "stash", "list"], mock_config)
        assert result == "stash@{0}: WIP on main"

    @patch("git_acp.git.management.run_git_command")
    @patch("git_acp.git.management.debug_item")
    def test_manage_stash__verbose_logs_debug(
        self,
        mock_debug_item: MagicMock,
        mock_run: MagicMock,
        verbose_config: GitConfig,
    ) -> None:
        """Log debug output in verbose mode."""
        mock_run.return_value = ("", "")

        manage_stash("save", config=verbose_config)

        mock_debug_item.assert_called()

    @patch("git_acp.git.management.run_git_command")
    def test_manage_stash__raises_git_error_on_failure(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Raise GitError when stash operation fails."""
        mock_run.side_effect = GitError("no local changes to save")

        with pytest.raises(GitError) as exc:
            manage_stash("save", config=mock_config)

        assert "Failed to save stash" in str(exc.value)

    @patch("git_acp.git.management.run_git_command")
    def test_manage_stash__save_returns_none(
        self, mock_run: MagicMock, mock_config: GitConfig
    ) -> None:
        """Return None for non-list operations."""
        mock_run.return_value = ("", "")

        result = manage_stash("save", config=mock_config)

        assert result is None
