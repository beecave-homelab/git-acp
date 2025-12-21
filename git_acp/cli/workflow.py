"""Git workflow orchestration.

This module provides the GitWorkflow class that coordinates the git-acp
workflow using injected dependencies for user interaction.
"""

from __future__ import annotations

import shlex
from typing import TYPE_CHECKING

from git_acp.ai import generate_commit_message
from git_acp.config import COLORS
from git_acp.git import (
    CommitType,
    GitError,
    classify_commit_type,
    get_changed_files,
    get_current_branch,
    git_add,
    git_commit,
    git_push,
    unstage_files,
)

if TYPE_CHECKING:
    from git_acp.cli.interaction import UserInteraction
    from git_acp.utils import GitConfig


class GitWorkflow:
    """Orchestrates the git add-commit-push workflow.

    This class coordinates all git operations and user interactions,
    delegating I/O to the injected UserInteraction implementation.
    """

    def __init__(
        self,
        config: GitConfig,
        interaction: UserInteraction,
        *,
        files_from_cli: bool = False,
        commit_type_override: str | None = None,
    ) -> None:
        """Initialize the workflow.

        Args:
            config: Git configuration options.
            interaction: User interaction implementation.
            files_from_cli: True if files were specified via -a flag. Enables
                additional validation after staging.
            commit_type_override: If provided, use this commit type instead of
                auto-classification (from -t flag).
        """
        self.config = config
        self.interaction = interaction
        self._files_from_cli = files_from_cli
        self._commit_type_override = commit_type_override

    def run(self) -> int:
        """Execute the git-acp workflow.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        try:
            # Handle interactive file selection if needed
            if not self._handle_file_selection():
                return 0  # No files to process, clean exit

            # Detect branch if not specified
            if not self._handle_branch_detection():
                return 1

            # Add files
            if not self._handle_git_add():
                return 1

            # Check if anything was staged (for -a flag case)
            if self._files_from_cli and not self._check_staged_files():
                return 0  # Clean exit, nothing to commit

            # Generate or validate commit message
            if not self._handle_commit_message():
                return 1

            # Classify and select commit type
            selected_type = self._handle_commit_type()
            if selected_type is None:
                return 1

            # Format message
            formatted_message = self._format_message(selected_type)

            # Confirm with user (if not skipping)
            if not self._handle_confirmation(formatted_message):
                return 0  # User cancelled, clean exit

            # Handle dry-run mode
            if self.config.dry_run:
                self._handle_dry_run(formatted_message)
                return 0

            # Commit and push
            if not self._handle_commit(formatted_message):
                return 1

            if not self._handle_push():
                return 1

            return 0

        except Exception as e:
            unstage_files()
            self.interaction.print_error(
                f"An unexpected error occurred:\n{e}",
                "Please report this issue if it persists.",
                "Unexpected Error",
            )
            return 1

    def _handle_file_selection(self) -> bool:
        """Handle file selection phase.

        Returns:
            True if files are ready to process, False to exit cleanly.
        """
        # If files were specified via -a flag, accept them even if it is "."
        if self._files_from_cli:
            return True

        # If files are set in config (not via CLI flag) and not default "."
        if self.config.files and self.config.files != ".":
            return True

        # Interactive file selection
        try:
            changed_files = get_changed_files(self.config)
            if not changed_files:
                if self.config.skip_confirmation:
                    self.interaction.print_panel(
                        "No changes detected in the repository. Nothing to do.",
                        "No Changes",
                        "yellow",
                    )
                    return False
                # select_files will raise for empty set

            self.config.files = self.interaction.select_files(changed_files)
            return True

        except GitError as e:
            if "cancelled by user" in str(e).lower():
                unstage_files()
                self.interaction.print_panel(
                    "Operation cancelled by user.",
                    "Cancelled",
                    "yellow",
                )
            else:
                self.interaction.print_error(
                    f"Error during file selection:\n{e}",
                    "Check file paths and try again.",
                    "File Selection Failed",
                )
            return False

    def _handle_branch_detection(self) -> bool:
        """Detect current branch if not specified.

        Returns:
            True if branch is set, False on error.
        """
        if self.config.branch:
            return True

        try:
            self.config.branch = get_current_branch()
            return True
        except GitError as e:
            self.interaction.print_error(
                f"Error getting current branch:\n{e}",
                "Ensure you're in a git repository with a valid branch.",
                "Branch Detection Failed",
            )
            return False

    def _handle_git_add(self) -> bool:
        """Stage files for commit.

        Returns:
            True if successful, False on error.
        """
        try:
            # When files were provided via -a, mirror the interactive
            # "All files" UX by listing the files being staged.
            if self._files_from_cli:
                try:
                    changed_files = get_changed_files(self.config)
                except GitError:
                    changed_files = set()

                if changed_files:
                    cli_targets = shlex.split(self.config.files or "")
                    files_to_list = set(changed_files)

                    # When using -a . (or equivalent), show all changed files.
                    if cli_targets and not any(
                        target in {".", "./"} for target in cli_targets
                    ):
                        # Otherwise, only list files that would be affected by
                        # the resolved CLI targets (files/dirs).
                        files_to_list = {
                            path
                            for path in changed_files
                            if any(
                                path == target
                                or path.startswith(target.rstrip("/") + "/")
                                for target in cli_targets
                            )
                        }

                    if files_to_list:
                        self.interaction.print_message("Adding files:")
                        for file in sorted(files_to_list):
                            self.interaction.print_message(f"  - {file}")

            git_add(self.config.files, self.config)
            return True
        except GitError as e:
            self.interaction.print_error(
                f"Error adding files:\n{e}",
                "Check file paths and repository permissions.",
                "Git Add Failed",
            )
            return False

    def _check_staged_files(self) -> bool:
        """Check if any files were actually staged.

        Used when files are specified via -a flag to detect if the specified
        files had any actual changes.

        Returns:
            True if files are staged, False if nothing was staged.
        """
        staged_files = get_changed_files(self.config, staged_only=True)
        if not staged_files:
            msg = (
                f"No actual changes were found in the files/patterns "
                f"specified by -a (resolved to: '{self.config.files}'). "
                "Nothing was staged."
            )
            self.interaction.print_panel(msg, "No Changes Staged via -a", "yellow")
            return False
        return True

    def _handle_commit_message(self) -> bool:
        """Generate or validate commit message.

        Returns:
            True if message is ready, False on error.
        """
        if self.config.use_ollama:
            try:
                self.config.message = generate_commit_message(self.config)
            except GitError as e:
                self.interaction.print_error(
                    f"AI commit message generation failed:\n{e}",
                    "Check Ollama server status and configuration.",
                    "AI Generation Failed",
                )
                if not self.interaction.confirm(
                    "Would you like to continue with a manual commit message?"
                ):
                    unstage_files()
                    return False
                manual_message = self._prompt_manual_message()
                if not manual_message:
                    unstage_files()
                    self.interaction.print_error(
                        "No commit message provided.",
                        "Please specify a message with -m or use --ollama.",
                        "Missing Message",
                    )
                    return False

                self.config.message = manual_message

        if not self.config.message:
            manual_message = self._prompt_manual_message()
            if manual_message:
                self.config.message = manual_message
            else:
                unstage_files()
                self.interaction.print_error(
                    "No commit message provided.",
                    "Please specify a message with -m or use --ollama.",
                    "Missing Message",
                )
                return False

        return True

    def _prompt_manual_message(self) -> str | None:
        """Prompt the user for a manual commit message if supported.

        Returns:
            The commit message entered by the user, or None if prompting is not
            supported.
        """
        prompt_manual = getattr(self.interaction, "_prompt_manual_commit_message", None)
        if callable(prompt_manual):
            return prompt_manual()
        return None

    def _handle_commit_type(self) -> CommitType | None:
        """Classify and select commit type.

        Returns:
            Selected commit type, or None on error.
        """
        bold = COLORS["bold"]
        success = COLORS["success"]

        # Use override if provided via -t flag
        if self._commit_type_override:
            try:
                selected_type = CommitType.from_str(self._commit_type_override)
                self.interaction.print_message(
                    f"[{bold}]🤖 Analyzing changes to suggest commit type...[/{bold}]"
                )
                self.interaction.print_message(
                    f"[{success}]✓ Using specified commit type: "
                    f"{selected_type.value}[/{success}]"
                )
                return selected_type
            except GitError as e:
                self.interaction.print_error(
                    f"Invalid commit type specified:\n{e}",
                    "Use: feat, fix, docs, style, refactor, test, chore, revert.",
                    "Invalid Commit Type",
                )
                return None

        # Auto-classify commit type
        try:
            commit_message = self.config.message or ""
            suggested_type = classify_commit_type(self.config, commit_message)
        except GitError as e:
            self.interaction.print_error(
                f"Error determining commit type:\n{e}",
                "Check your changes or specify a commit type with -t.",
                "Commit Type Error",
            )
            return None

        self.interaction.print_message(
            f"[{bold}]🤖 Analyzing changes to suggest commit type...[/{bold}]"
        )

        try:
            selected_type = self.interaction.select_commit_type(
                suggested_type, self.config, commit_message
            )
            self.interaction.print_message(
                f"[{success}]✓ Commit type selected successfully[/{success}]"
            )
            return selected_type
        except GitError as e:
            if "cancelled by user" in str(e).lower():
                self.interaction.print_panel(
                    "Operation cancelled by user.",
                    "Cancelled",
                    "yellow",
                )
            else:
                self.interaction.print_error(
                    f"Error selecting commit type:\n{e}",
                    "Try again or specify a commit type with -t.",
                    "Commit Type Selection Failed",
                )
            unstage_files()
            return None

    def _format_message(self, commit_type: CommitType) -> str:
        """Format commit message with type prefix.

        Args:
            commit_type: The commit type to use.

        Returns:
            Formatted commit message.
        """
        lines = self.config.message.split("\n")
        title = lines[0]
        description = "\n".join(lines[1:])
        return f"{commit_type.value}: {title}\n\n{description}".strip()

    def _handle_confirmation(self, formatted_message: str) -> bool:
        """Show message and ask for confirmation.

        Args:
            formatted_message: The formatted commit message.

        Returns:
            True to proceed, False to cancel.
        """
        header = COLORS["ai_message_header"]

        if not self.config.skip_confirmation:
            self.interaction.print_message(
                f"[{header}]Commit Message:[/{header}]\n{formatted_message}"
            )
            if not self.interaction.confirm("Do you want to proceed?"):
                unstage_files()
                self.interaction.print_panel(
                    "Operation cancelled by user.",
                    "Cancelled",
                    "yellow",
                )
                return False
        else:
            # Only show auto-commit message if not in dry-run mode
            # (dry-run will show its own message)
            if not self.config.dry_run:
                self.interaction.print_message(
                    f"[{header}]Auto-committing with message:[/{header}]\n"
                    f"{formatted_message}"
                )

        return True

    def _handle_commit(self, formatted_message: str) -> bool:
        """Commit changes.

        Args:
            formatted_message: The commit message.

        Returns:
            True if successful, False on error.
        """
        try:
            git_commit(formatted_message)
            return True
        except GitError as e:
            self.interaction.print_error(
                f"Error committing changes:\n{e}",
                "Check if there are changes to commit and try again.",
                "Commit Failed",
            )
            return False

    def _handle_push(self) -> bool:
        """Push changes to remote.

        Returns:
            True if successful, False on error.
        """
        try:
            git_push(self.config.branch)
            return True
        except GitError as e:
            self.interaction.print_error(
                f"Error pushing changes:\n{e}",
                "Pull latest changes, resolve conflicts, and try again.",
                "Push Failed",
            )
            return False

    def _handle_dry_run(self, formatted_message: str) -> None:
        """Handle dry-run mode by showing what would be committed.

        Args:
            formatted_message: The formatted commit message that would be used.
        """
        status = COLORS["status"]
        success = COLORS["success"]

        self.interaction.print_message(
            f"[{status}]🔍 DRY RUN MODE - No changes will be committed[/{status}]"
        )
        self.interaction.print_message(
            f"[{success}]Would commit with message:[/{success}]\n{formatted_message}"
        )

        # Unstage files since we're not actually committing
        try:
            unstage_files()
            self.interaction.print_message(
                f"[{status}]Files have been unstaged (dry-run cleanup)[/{status}]"
            )
        except GitError:
            # If unstaging fails, it's not critical for dry-run
            if self.config.verbose:
                self.interaction.print_message(
                    f"[{status}]Note: Could not unstage files (dry-run cleanup)[/{status}]"
                )
