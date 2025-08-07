# Refactor Summary

## Overview
- Separated AI communication logic from commit message utilities by introducing `git_acp/ai/client.py`.
- Extracted commit history helpers into `git_acp/git/history.py` so `git_operations.py` focuses on core Git commands.

## Details
- **git_acp/ai/ai_utils.py**
  - Removed `AIClient` class and related imports.
  - Now concentrates on prompt construction, context gathering, and message editing.
  - Imports `AIClient` from the new `client` module for message generation.
- **git_acp/ai/client.py**
  - New module containing `AIClient` responsible for interacting with OpenAI-compatible endpoints.
  - Isolates network concerns from commit message logic and supports test patching of `OpenAI` via `ai_utils`.
- **git_acp/git/git_operations.py**
  - Slimmed to core repository actions (add, commit, push, diffs, etc.).
  - Delegates commit history analysis to the new `history` module while re-exporting legacy helpers.
- **git_acp/git/history.py**
  - New module with `get_recent_commits`, `find_related_commits`, and `analyze_commit_patterns`.
  - Provides focused commit history and analysis utilities.
- **project-overview.md**
  - Updated project structure to document new modules and responsibilities.

## Rationale
These changes apply separation of concerns, isolating AI network operations from message handling and splitting git history analysis from general git commands. The result is clearer module boundaries and improved maintainability.
