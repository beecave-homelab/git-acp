"""Tests for GitWorkflow with dependency injection.

This module tests the workflow orchestration using injected UserInteraction,
enabling comprehensive testing without interactive prompts.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from git_acp.cli.interaction import CancelledByUserError, TestInteraction
from git_acp.cli.workflow import EXIT_CODE_CANCELLED, GitWorkflow
from git_acp.git import CommitType, GitError
from git_acp.utils import GitConfig


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def mock_config() -> GitConfig:
    """Create a non-interactive GitConfig instance.

    Returns:
        GitConfig: Test configuration with skip_confirmation=True.
    """
    return GitConfig(
        files="test.py",
        message="Test commit",
        branch="main",
        use_ollama=False,
        interactive=False,
        skip_confirmation=True,
        verbose=False,
        prompt_type="simple",
    )


@pytest.fixture
def interactive_config() -> GitConfig:
    """Create an interactive GitConfig instance.

    Returns:
        GitConfig: Test configuration with skip_confirmation=False.
    """
    return GitConfig(
        files=".",
        message=None,
        branch=None,
        use_ollama=True,
        interactive=True,
        skip_confirmation=False,
        verbose=False,
        prompt_type="advanced",
    )


# -----------------------------------------------------------------------------
# Tests for UserInteraction Protocol
# -----------------------------------------------------------------------------
class TestUserInteractionProtocol:
    """Test that UserInteraction protocol is properly defined."""

    def test_user_interaction_protocol_exists(self) -> None:
        """UserInteraction protocol should be importable."""
        from git_acp.cli.interaction import UserInteraction

        # Protocol should have required methods
        assert hasattr(UserInteraction, "select_files")
        assert hasattr(UserInteraction, "select_commit_type")
        assert hasattr(UserInteraction, "confirm")
        assert hasattr(UserInteraction, "print_message")
        assert hasattr(UserInteraction, "print_error")
        assert hasattr(UserInteraction, "print_panel")


class TestTestInteraction:
    """Test the TestInteraction stub for testing workflows."""

    def test_test_interaction_select_files(self) -> None:
        """TestInteraction should return canned file selection."""
        from git_acp.cli.interaction import TestInteraction

        interaction = TestInteraction(files_response="file1.py file2.py")
        result = interaction.select_files({"file1.py", "file2.py", "file3.py"})

        assert result == "file1.py file2.py"

    def test_test_interaction_select_commit_type(self, mock_config: GitConfig) -> None:
        """TestInteraction should return canned commit type."""
        from git_acp.cli.interaction import TestInteraction

        interaction = TestInteraction(commit_type_response=CommitType.FEAT)
        result = interaction.select_commit_type(CommitType.CHORE, mock_config, "Test")

        assert result == CommitType.FEAT

    def test_test_interaction_confirm(self) -> None:
        """TestInteraction should return canned confirmation."""
        from git_acp.cli.interaction import TestInteraction

        interaction = TestInteraction(confirm_response=False)
        result = interaction.confirm("Proceed?")

        assert result is False

    def test_test_interaction_print_methods_are_noop(self) -> None:
        """TestInteraction print methods should not raise."""
        from git_acp.cli.interaction import TestInteraction

        interaction = TestInteraction()

        # These should not raise
        interaction.print_message("test")
        interaction.print_error("error", "suggestion", "title")
        interaction.print_panel("content", "title", "style")


# -----------------------------------------------------------------------------
# Tests for GitWorkflow
# -----------------------------------------------------------------------------
class TestGitWorkflow:
    """Test GitWorkflow orchestration with injected dependencies."""

    def test_workflow_init(self, mock_config: GitConfig) -> None:
        """GitWorkflow should accept config and interaction."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        assert workflow.config is mock_config
        assert workflow.interaction is interaction

    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.git_push")
    def test_workflow_run__success_non_interactive(
        self,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_add: MagicMock,
        mock_classify: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Run workflow successfully in non-interactive mode."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_classify.return_value = CommitType.CHORE

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 0
        mock_add.assert_called_once()
        mock_commit.assert_called_once()
        mock_push.assert_called_once()

    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.get_changed_files")
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.git_push")
    def test_workflow_run__interactive_file_selection(
        self,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_add: MagicMock,
        mock_get_changed: MagicMock,
        mock_classify: MagicMock,
        interactive_config: GitConfig,
    ) -> None:
        """Use interaction.select_files when files not specified."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_get_changed.return_value = {"file1.py", "file2.py"}
        mock_classify.return_value = CommitType.FEAT

        interaction = TestInteraction(
            files_response="file1.py",
            commit_type_response=CommitType.FEAT,
            confirm_response=True,
        )
        # Set message so we don't need AI
        interactive_config.message = "Test message"
        interactive_config.use_ollama = False

        workflow = GitWorkflow(interactive_config, interaction)
        exit_code = workflow.run()

        assert exit_code == 0
        assert workflow.config.files == "file1.py"

    @patch("git_acp.cli.workflow.git_add")
    def test_workflow_run__git_add_failure(
        self,
        mock_add: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Return non-zero exit code when git add fails."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_add.side_effect = GitError("Failed to add files")

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 1

    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.generate_commit_message")
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.git_push")
    def test_workflow__ai_failure_user_accepts_manual(
        self,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_add: MagicMock,
        mock_generate: MagicMock,
        mock_classify: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Handle AI failure when user accepts manual message fallback."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_config.use_ollama = True
        mock_config.message = None
        mock_generate.side_effect = GitError("AI unavailable")
        mock_classify.return_value = CommitType.CHORE

        interaction = TestInteraction(
            confirm_response=True,
            manual_message_response="Manual commit message",
        )
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 0
        assert workflow.config.message == "Manual commit message"
        mock_generate.assert_called_once()
        mock_add.assert_called_once()
        mock_commit.assert_called_once()
        mock_push.assert_called_once()

    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.git_commit")
    def test_workflow_run__git_commit_failure(
        self,
        mock_commit: MagicMock,
        mock_add: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Return non-zero exit code when git commit fails."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_commit.side_effect = GitError("Nothing to commit")

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 1

    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.git_push")
    def test_workflow_run__git_push_failure(
        self,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_add: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Return non-zero exit code when git push fails."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_push.side_effect = GitError("Failed to push")

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 1

    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.unstage_files")
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.git_push")
    def test_workflow_run__user_cancels_confirmation(
        self,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_add: MagicMock,
        mock_unstage: MagicMock,
        mock_classify: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Return cancellation exit code when user cancels at confirmation."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_config.skip_confirmation = False
        mock_classify.return_value = CommitType.CHORE

        interaction = TestInteraction(confirm_response=False)
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == EXIT_CODE_CANCELLED
        mock_unstage.assert_called_once_with()
        mock_commit.assert_not_called()
        mock_push.assert_not_called()

    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.generate_commit_message")
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.git_push")
    def test_workflow_run__uses_ai_for_message(
        self,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_add: MagicMock,
        mock_generate: MagicMock,
        mock_classify: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Use AI to generate commit message when use_ollama is True."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_config.use_ollama = True
        mock_config.message = None
        mock_generate.return_value = "AI generated message"
        mock_classify.return_value = CommitType.CHORE

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 0
        mock_generate.assert_called_once()
        assert workflow.config.message == "AI generated message"

    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.git_push")
    def test_workflow_run__classifies_commit_type(
        self,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_add: MagicMock,
        mock_classify: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Classify commit type based on changes."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_classify.return_value = CommitType.FIX

        interaction = TestInteraction(commit_type_response=CommitType.FIX)
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 0
        mock_classify.assert_called_once()

    @patch("git_acp.cli.workflow.get_changed_files")
    @patch("git_acp.cli.workflow.git_add")
    def test_handle_git_add__cli_add_filters_to_cli_targets(
        self,
        mock_add: MagicMock,
        mock_get_changed: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """List only files matching CLI -a targets when files_from_cli is True."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_config.files = "tests"
        mock_config.message = "Test commit"
        mock_config.use_ollama = False

        mock_get_changed.return_value = {
            "tests/ai/test_ai_utils.py",
            "tests/git/test_history.py",
            "git_acp/cli/workflow.py",
        }

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction, files_from_cli=True)

        result = workflow._handle_git_add()

        assert result is True
        mock_add.assert_called_once_with(mock_config.files, mock_config)

        # First message is the header, followed by per-file lines.
        assert interaction.messages[0] == "Adding files:"
        listed_files = interaction.messages[1:]
        assert any("tests/ai/test_ai_utils.py" in msg for msg in listed_files)
        assert any("tests/git/test_history.py" in msg for msg in listed_files)
        assert all("git_acp/cli/workflow.py" not in msg for msg in listed_files)

    @patch("git_acp.cli.workflow.unstage_files")
    @patch("git_acp.cli.workflow.git_push")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.get_current_branch")
    @patch("git_acp.cli.workflow.get_changed_files")
    def test_workflow_run__dry_run_with_cli_files_shows_preview(
        self,
        mock_get_changed: MagicMock,
        mock_branch: MagicMock,
        mock_add: MagicMock,
        mock_classify: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        mock_unstage: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Reach dry-run output even though git_add is skipped in dry-run."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_config.files = "."
        mock_config.message = "Test commit message"
        mock_config.use_ollama = False
        mock_config.skip_confirmation = True
        mock_config.dry_run = True

        mock_get_changed.return_value = {"file1.py"}
        mock_branch.return_value = "main"
        mock_classify.return_value = CommitType.CHORE

        interaction = TestInteraction(confirm_response=True)
        workflow = GitWorkflow(
            mock_config,
            interaction,
            files_from_cli=True,
            raw_add_patterns=".",
        )

        exit_code = workflow.run()

        assert exit_code == 0
        assert any("DRY RUN MODE" in msg for msg in interaction.messages)
        assert any("Would commit with message" in msg for msg in interaction.messages)
        mock_commit.assert_not_called()
        mock_push.assert_not_called()

    @patch("git_acp.cli.workflow.unstage_files")
    @patch("git_acp.cli.workflow.git_push")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.get_current_branch")
    @patch("git_acp.cli.workflow.get_changed_files")
    def test_dry_run_uses_working_tree_not_staged_for_check(
        self,
        mock_get_changed: MagicMock,
        mock_branch: MagicMock,
        mock_add: MagicMock,
        mock_classify: MagicMock,
        mock_commit: MagicMock,
        mock_push: MagicMock,
        mock_unstage: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Regression: dry-run with -a must check working tree, not staged files.

        In dry-run mode, git_add skips staging. The _check_staged_files method
        must use staged_only=False to validate working tree changes exist,
        not staged_only=True which would always be empty in dry-run.

        Bug scenario: without the fix, dry-run with -a would incorrectly show
        "No Changes Staged via -a" because it checked staged files (empty)
        instead of working tree files (present).
        """
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_config.files = "."
        mock_config.message = "Test commit message"
        mock_config.use_ollama = False
        mock_config.skip_confirmation = True
        mock_config.dry_run = True

        def get_changed_side_effect(
            config: GitConfig, staged_only: bool = False
        ) -> set[str]:
            if staged_only:
                return set()  # No staged files (dry-run skipped staging)
            return {"file1.py", "file2.py"}  # Working tree has changes

        mock_get_changed.side_effect = get_changed_side_effect
        mock_branch.return_value = "main"
        mock_classify.return_value = CommitType.CHORE

        interaction = TestInteraction(confirm_response=True)
        workflow = GitWorkflow(
            mock_config,
            interaction,
            files_from_cli=True,
            raw_add_patterns=".",
        )

        exit_code = workflow.run()

        # Must succeed and show dry-run output, NOT "No Changes Staged via -a"
        assert exit_code == 0
        assert any("DRY RUN MODE" in msg for msg in interaction.messages)
        # Verify no "No Changes Staged" error panel was shown
        no_staged_panels = [
            p for p in interaction.panels if "No Changes Staged" in p[1]
        ]
        assert not no_staged_panels, (
            "Dry-run should not show 'No Changes Staged via -a' when working "
            "tree has changes"
        )


# -----------------------------------------------------------------------------
# Tests for format_commit_message (pure function, easy to test)
# -----------------------------------------------------------------------------
class TestWorkflowErrorPaths:
    """Test GitWorkflow error handling paths."""

    @patch("git_acp.cli.workflow.get_changed_files")
    def test_workflow__no_changes_skip_confirmation(
        self,
        mock_get_changed: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Exit cleanly when no changes and skip_confirmation is True."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_get_changed.return_value = set()
        mock_config.files = "."  # Trigger file selection

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 0
        assert any("No changes" in p[0] for p in interaction.panels)

    @patch("git_acp.cli.workflow.unstage_files")
    @patch("git_acp.cli.workflow.get_changed_files")
    def test_workflow__file_selection_cancelled(
        self,
        mock_get_changed: MagicMock,
        mock_unstage: MagicMock,
        interactive_config: GitConfig,
    ) -> None:
        """Return cancellation exit code when file selection is cancelled."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_get_changed.return_value = {"README.md"}

        class CancellingInteraction(TestInteraction):
            def select_files(self, changed_files: set[str]) -> str:
                """Raise cancellation from the interactive file picker.

                Raises:
                    CancelledByUserError: Always raised for this test double.
                """
                raise CancelledByUserError("Operation cancelled by user.")

        interaction = CancellingInteraction()
        workflow = GitWorkflow(interactive_config, interaction)

        exit_code = workflow.run()

        assert exit_code == EXIT_CODE_CANCELLED
        mock_unstage.assert_called()

    @patch("git_acp.cli.workflow.get_current_branch")
    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__branch_detection_failure(
        self,
        mock_add: MagicMock,
        mock_branch: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Handle branch detection failure."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_config.branch = None
        mock_branch.side_effect = GitError("Not a git repository")

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 1
        assert any("Branch Detection" in e[2] for e in interaction.errors)

    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.unstage_files")
    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__commit_type_classification_failure(
        self,
        mock_add: MagicMock,
        mock_unstage: MagicMock,
        mock_classify: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Handle commit type classification failure."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_classify.side_effect = GitError("Cannot classify")

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 1
        mock_unstage.assert_not_called()
        assert any("Commit Type Error" in e[2] for e in interaction.errors)

    @patch("git_acp.cli.workflow.generate_commit_message")
    @patch("git_acp.cli.workflow.unstage_files")
    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__ai_failure_user_declines_manual(
        self,
        mock_add: MagicMock,
        mock_unstage: MagicMock,
        mock_generate: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Handle AI failure when user declines manual message."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_config.use_ollama = True
        mock_config.message = None
        mock_generate.side_effect = GitError("AI unavailable")

        interaction = TestInteraction(confirm_response=False)
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == EXIT_CODE_CANCELLED
        mock_unstage.assert_called_once_with()

    @patch("git_acp.cli.workflow.unstage_files")
    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__no_message_provided(
        self,
        mock_add: MagicMock,
        mock_unstage: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Handle missing commit message."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_config.message = None
        mock_config.use_ollama = False

        interaction = TestInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 1
        mock_unstage.assert_called_once_with()
        assert any("Missing Message" in e[2] for e in interaction.errors)

    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.unstage_files")
    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__commit_type_selection_cancelled(
        self,
        mock_add: MagicMock,
        mock_unstage: MagicMock,
        mock_classify: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Return cancellation exit code when commit type selection is cancelled."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_classify.return_value = CommitType.CHORE

        # Create interaction that raises on select_commit_type
        class CancellingInteraction(TestInteraction):
            def select_commit_type(
                self, suggested: CommitType, config: GitConfig, commit_message: str
            ) -> CommitType:
                raise CancelledByUserError("Operation cancelled by user.")

        interaction = CancellingInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == EXIT_CODE_CANCELLED
        mock_unstage.assert_called_once_with()

    @patch("git_acp.cli.workflow.unstage_files")
    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__manual_message_prompt_cancelled(
        self,
        mock_add: MagicMock,
        mock_unstage: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Return cancellation exit code when manual message prompt is cancelled."""
        mock_config.message = None
        mock_config.use_ollama = False

        class CancellingInteraction(TestInteraction):
            def _prompt_manual_commit_message(self) -> str | None:
                raise CancelledByUserError("Operation cancelled by user.")

        interaction = CancellingInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == EXIT_CODE_CANCELLED
        mock_unstage.assert_called_once_with()

    @patch("git_acp.cli.workflow.generate_commit_message")
    @patch("git_acp.cli.workflow.unstage_files")
    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__ai_fallback_manual_message_prompt_cancelled(
        self,
        mock_add: MagicMock,
        mock_unstage: MagicMock,
        mock_generate: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Return cancellation exit code when AI fallback prompt is cancelled."""
        mock_config.use_ollama = True
        mock_config.message = None
        mock_generate.side_effect = GitError("AI unavailable")

        class CancellingInteraction(TestInteraction):
            def _prompt_manual_commit_message(self) -> str | None:
                raise CancelledByUserError("Operation cancelled by user.")

        interaction = CancellingInteraction(confirm_response=True)
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == EXIT_CODE_CANCELLED
        mock_unstage.assert_called_once_with()


class TestFormatCommitMessage:
    """Test commit message formatting."""

    def test_format_commit_message__single_line(self) -> None:
        """Format single-line message with commit type prefix."""
        from git_acp.cli.cli import format_commit_message

        result = format_commit_message(CommitType.FEAT, "add new feature")

        # CommitType.FEAT.value includes emoji, e.g. "feat ✨"
        assert result.startswith(CommitType.FEAT.value)
        assert "add new feature" in result

    def test_format_commit_message__multi_line(self) -> None:
        """Format multi-line message with type prefix and body."""
        from git_acp.cli.cli import format_commit_message

        result = format_commit_message(
            CommitType.FIX, "fix bug\n\nDetailed description"
        )

        assert result.startswith(CommitType.FIX.value)
        assert "fix bug" in result
        assert "Detailed description" in result

    def test_format_commit_message__strips_trailing_whitespace(self) -> None:
        """Strip trailing whitespace from formatted message."""
        from git_acp.cli.cli import format_commit_message

        result = format_commit_message(CommitType.DOCS, "update readme\n\n")

        assert result.startswith(CommitType.DOCS.value)
        assert result.endswith("update readme")


class TestWorkflowFormatMessage:
    """Tests for GitWorkflow._format_message normalization behavior."""

    def test_format_message__does_not_duplicate_existing_prefix(self) -> None:
        """Keep a single prefix when AI output already contains one."""
        config = GitConfig(
            files="test.py",
            message="fix 🐛: add validation",
            branch="main",
            use_ollama=False,
            interactive=False,
            skip_confirmation=True,
            verbose=False,
            prompt_type="simple",
        )
        workflow = GitWorkflow(config, TestInteraction())

        assert workflow._format_message(CommitType.FIX) == "fix 🐛: add validation"

    def test_format_message__replaces_existing_prefix_when_type_changes(self) -> None:
        """Replace existing prefix and scope with selected classification type."""
        config = GitConfig(
            files="test.py",
            message="fix(auth): add validation",
            branch="main",
            use_ollama=False,
            interactive=False,
            skip_confirmation=True,
            verbose=False,
            prompt_type="simple",
        )
        workflow = GitWorkflow(config, TestInteraction())

        assert workflow._format_message(CommitType.FEAT) == "feat ✨: add validation"

    def test_format_message__strips_breaking_indicator_when_type_changes(self) -> None:
        """Remove breaking-change "!" indicator when replacing the prefix."""
        config = GitConfig(
            files="test.py",
            message="fix!: add validation",
            branch="main",
            use_ollama=False,
            interactive=False,
            skip_confirmation=True,
            verbose=False,
            prompt_type="simple",
        )
        workflow = GitWorkflow(config, TestInteraction())

        assert workflow._format_message(CommitType.FEAT) == "feat ✨: add validation"

    def test_format_message__adds_prefix_when_missing(self) -> None:
        """Add selected prefix when AI output has no conventional prefix."""
        config = GitConfig(
            files="test.py",
            message="add new feature",
            branch="main",
            use_ollama=False,
            interactive=False,
            skip_confirmation=True,
            verbose=False,
            prompt_type="simple",
        )
        workflow = GitWorkflow(config, TestInteraction())

        assert workflow._format_message(CommitType.FEAT) == "feat ✨: add new feature"
