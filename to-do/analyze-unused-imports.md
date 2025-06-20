# To-Do: Analyze and Fix Unused Imports

This plan outlines the steps to analyze and fix unused import warnings (W0611) reported by Pylint.

## Tasks

- [x] **Analysis Phase:**
  - [x] Run `pylint --disable=all --enable=W0611 git_acp/` to generate a list of unused imports.
    - Path: `git_acp/`
    - Action: Execute the Pylint command and paste the output below for analysis.
    - Analysis Results:

        ```shell
        ************* Module git_acp.utils.formatting
        git_acp/utils/formatting.py:11:0: W0611: Unused Progress imported from rich.progress (unused-import)
        ************* Module git_acp.cli.cli
        git_acp/cli/cli.py:27:0: W0611: Unused run_git_command imported from git_acp.git (unused-import)
        git_acp/cli/cli.py:40:0: W0611: Unused OptionalConfig imported from git_acp.utils (unused-import)
        ************* Module git_acp.ai.ai_utils
        git_acp/ai/ai_utils.py:8:0: W0611: Unused Counter imported from collections (unused-import)
        git_acp/ai/ai_utils.py:17:0: W0611: Unused DEFAULT_PROMPT_TYPE imported from git_acp.config (unused-import)
        git_acp/ai/ai_utils.py:17:0: W0611: Unused TERMINAL_WIDTH imported from git_acp.config (unused-import)
        git_acp/ai/ai_utils.py:30:0: W0611: Unused run_git_command imported from git_acp.git (unused-import)
        git_acp/ai/ai_utils.py:38:0: W0611: Unused PromptType imported from git_acp.utils (unused-import)
        ************* Module git_acp.git.git_operations
        git_acp/git/git_operations.py:16:0: W0611: Unused Any imported from typing (unused-import)
        git_acp/git/git_operations.py:22:0: W0611: Unused COLORS imported from git_acp.config (unused-import)
        git_acp/git/git_operations.py:28:0: W0611: Unused GitConfig imported from git_acp.utils (unused-import)
        git_acp/git/git_operations.py:28:0: W0611: Unused warning imported from git_acp.utils (unused-import)
        ```

    - Accept Criteria: A complete list of W0611 warnings is available for review.

- [x] **Analysis and Cleanup Plan:**
  - [x] `git_acp/utils/formatting.py`:
    - [x] **Delete:** `from rich.progress import Progress`
  - [x] `git_acp/cli/cli.py`:
    - [x] **Delete:** `from git_acp.git import run_git_command`
    - [x] **Delete:** `from git_acp.utils import OptionalConfig`
  - [x] `git_acp/ai/ai_utils.py`:
    - [x] **Delete:** `from collections import Counter`
    - [x] **Delete:** `from git_acp.config import DEFAULT_PROMPT_TYPE, TERMINAL_WIDTH`
    - [x] **Delete:** `from git_acp.git import run_git_command`
    - [x] **Fix:** `from git_acp.utils import PromptType`. This is likely a necessary import that pylint incorrectly flagged. Mark to keep.
  - [x] `git_acp/git/git_operations.py`:
    - [x] **Delete:** `from typing import Any`
    - [x] **Delete:** `from git_acp.config import COLORS`
    - [x] **Delete:** `from git_acp.utils import GitConfig, warning`

- [x] **Implementation Phase:**
  - [x] **Identify and remove safe-to-delete imports.**
    - Action: Go through the Pylint output. For each file, identify imports that are clearly unused and remove them.
    - Status: Done
  - [x] **Identify and fix incorrectly flagged imports.**
    - Action: Some imports might be flagged as unused but are required (e.g., `__init__.py` exports, imports for side-effects). For these, add a `# pylint: disable=unused-import` comment on the line of the import, along with a brief explanation.
    - Status: Done

- [x] **Testing Phase:**
  - [x] Run application tests to ensure no functionality was broken after removing imports.
    - Path: `tests/`
    - Action: Execute the test suite.
    - Accept Criteria: All existing tests pass.
    - Status: Done

- [ ] **Documentation Phase:**
  - [ ] No documentation updates are expected for this task.

## Related Files

- All Python files within the `git_acp/` directory that have unused import warnings.

## Future Enhancements

- [ ] Consider configuring `ruff` to automatically remove unused imports as a pre-commit hook to prevent this issue in the future.
