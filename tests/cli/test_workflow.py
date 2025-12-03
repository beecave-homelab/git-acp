"""Tests for GitWorkflow with dependency injection.

This module tests the workflow orchestration using injected UserInteraction,
enabling comprehensive testing without interactive prompts.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

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
        result = interaction.select_commit_type(CommitType.CHORE, mock_config)

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
        assert interactive_config.files == "file1.py"

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
        assert mock_config.message == "Manual commit message"
        mock_generate.assert_called_once_with(mock_config)
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
    @patch("git_acp.cli.workflow.git_add")
    @patch("git_acp.cli.workflow.git_commit")
    @patch("git_acp.cli.workflow.git_push")
    def test_workflow_run__user_cancels_confirmation(
        self,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_add: MagicMock,
        mock_classify: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Return zero exit code when user cancels at confirmation."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_config.skip_confirmation = False
        mock_classify.return_value = CommitType.CHORE

        interaction = TestInteraction(confirm_response=False)
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 0
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
        mock_generate.assert_called_once_with(mock_config)
        assert mock_config.message == "AI generated message"

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

    @patch("git_acp.cli.workflow.get_changed_files")
    def test_workflow__file_selection_cancelled(
        self,
        mock_get_changed: MagicMock,
        interactive_config: GitConfig,
    ) -> None:
        """Handle user cancellation during file selection."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_get_changed.side_effect = GitError("Operation cancelled by user.")

        interaction = TestInteraction()
        workflow = GitWorkflow(interactive_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 0  # Clean exit on cancel

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
    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__commit_type_classification_failure(
        self,
        mock_add: MagicMock,
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
        assert any("Commit Type Error" in e[2] for e in interaction.errors)

    @patch("git_acp.cli.workflow.generate_commit_message")
    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__ai_failure_user_declines_manual(
        self,
        mock_add: MagicMock,
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

        assert exit_code == 1

    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__no_message_provided(
        self,
        mock_add: MagicMock,
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
        assert any("Missing Message" in e[2] for e in interaction.errors)

    @patch("git_acp.cli.workflow.classify_commit_type")
    @patch("git_acp.cli.workflow.git_add")
    def test_workflow__commit_type_selection_cancelled(
        self,
        mock_add: MagicMock,
        mock_classify: MagicMock,
        mock_config: GitConfig,
    ) -> None:
        """Handle cancellation during commit type selection."""
        from git_acp.cli.interaction import TestInteraction
        from git_acp.cli.workflow import GitWorkflow

        mock_classify.return_value = CommitType.CHORE

        # Create interaction that raises on select_commit_type
        class CancellingInteraction(TestInteraction):
            def select_commit_type(
                self, suggested: CommitType, config: GitConfig
            ) -> CommitType:
                raise GitError("Operation cancelled by user.")

        interaction = CancellingInteraction()
        workflow = GitWorkflow(mock_config, interaction)

        exit_code = workflow.run()

        assert exit_code == 1


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
