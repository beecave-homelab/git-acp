"""Tests for --auto-group CLI behavior."""

from __future__ import annotations

from unittest.mock import ANY, MagicMock, call, patch

from click.testing import CliRunner

from git_acp.cli.cli import main


class TestCliAutoGroup:
    """Tests for CLI auto-group orchestration."""

    def setup_method(self) -> None:
        """Set up a Click runner."""
        self.runner = CliRunner()

    @patch("git_acp.cli.cli.unstage_files")
    @patch("git_acp.cli.cli.GitWorkflow")
    @patch("git_acp.cli.cli.group_changed_files")
    @patch("git_acp.cli.cli.get_changed_files")
    def test_auto_group_blocks_when_staged_files_exist(
        self,
        mock_get_changed_files: MagicMock,
        mock_group_changed_files: MagicMock,
        mock_workflow_cls: MagicMock,
        mock_unstage: MagicMock,
    ) -> None:
        """Exit with code 1 when staging area is not empty."""
        mock_get_changed_files.side_effect = [
            {"already_staged.py"},
        ]

        result = self.runner.invoke(main, ["--auto-group", "--no-confirm"])

        assert result.exit_code == 1
        mock_group_changed_files.assert_not_called()
        mock_workflow_cls.assert_not_called()
        mock_unstage.assert_not_called()

    @patch("git_acp.cli.cli.unstage_files")
    @patch("git_acp.cli.cli.GitWorkflow")
    @patch("git_acp.cli.cli.group_changed_files")
    @patch("git_acp.cli.cli.get_changed_files")
    def test_auto_group_runs_workflow_for_each_group_and_cleans_staging(
        self,
        mock_get_changed_files: MagicMock,
        mock_group_changed_files: MagicMock,
        mock_workflow_cls: MagicMock,
        mock_unstage: MagicMock,
    ) -> None:
        """Call workflow.run once per group and unstage after each group."""
        mock_get_changed_files.side_effect = [
            set(),  # initial staged-only check
            {"a.py", "b.py"},  # changed-files set
            set(),  # staged-before group 1
            set(),  # staged-before group 2
        ]
        mock_group_changed_files.return_value = [["a.py"], ["b.py"]]

        workflow_one = MagicMock()
        workflow_one.run.return_value = 0
        workflow_two = MagicMock()
        workflow_two.run.return_value = 1
        mock_workflow_cls.side_effect = [workflow_one, workflow_two]

        result = self.runner.invoke(main, ["--auto-group", "--no-confirm"])

        assert result.exit_code == 1
        assert mock_workflow_cls.call_count == 2
        assert workflow_one.run.call_count == 1
        assert workflow_two.run.call_count == 1

        assert mock_unstage.call_args_list == [call(ANY), call(ANY)]

        first_config = mock_workflow_cls.call_args_list[0].args[0]
        second_config = mock_workflow_cls.call_args_list[1].args[0]

        assert first_config.files == "a.py"
        assert second_config.files == "b.py"
        assert first_config is not second_config

    @patch("git_acp.cli.cli.unstage_files")
    @patch("git_acp.cli.cli.GitWorkflow")
    @patch("git_acp.cli.cli.group_changed_files")
    @patch("git_acp.cli.cli.get_changed_files")
    def test_auto_group_continues_on_exception_and_reports_failure(
        self,
        mock_get_changed_files: MagicMock,
        mock_group_changed_files: MagicMock,
        mock_workflow_cls: MagicMock,
        mock_unstage: MagicMock,
    ) -> None:
        """Continue processing remaining groups when one workflow throws."""
        mock_get_changed_files.side_effect = [
            set(),
            {"a.py", "b.py"},
            set(),
            set(),
        ]
        mock_group_changed_files.return_value = [["a.py"], ["b.py"]]

        workflow_one = MagicMock()
        workflow_one.run.side_effect = RuntimeError("boom")
        workflow_two = MagicMock()
        workflow_two.run.return_value = 0
        mock_workflow_cls.side_effect = [workflow_one, workflow_two]

        result = self.runner.invoke(main, ["--auto-group", "--no-confirm"])

        assert result.exit_code == 1
        assert mock_workflow_cls.call_count == 2
        assert mock_unstage.call_count == 2
