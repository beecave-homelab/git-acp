"""Low-level Git command runner and error handler."""

import signal
import sys
from git_acp.git.status import unstage_files


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful interruption."""

    def signal_handler(*_):
        unstage_files()
        print("Operation cancelled by user.")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
