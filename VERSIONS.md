# VERSIONS.md

## Table of Contents

- [v0.18.0 (Current) - 02-12-2025](#v0180-current-02-12-2025)
- [v0.17.0 - 10-08-2025](#v0170-10-08-2025)
- [v0.16.0 - August 2025](#v0160-august-2025)
- [v0.15.1 - June 2025](#v0151-june-2025)
- [v0.15.0 - 01-02-2025](#v0150-01-02-2025)
- [v0.14.2 - 09-06-2025](#v0142-09-06-2025)
- [v0.14.1 - 28-01-2025](#v0141-28-01-2025)
- [v0.14.0 - 27-01-2025](#v0140-27-01-2025)
- [v0.13.4 - 26-01-2025](#v0134-26-01-2025)
- [v0.13.3 - 26-01-2025](#v0133-26-01-2025)
- [v0.13.2 - 26-01-2025](#v0132-26-01-2025)
- [v0.13.1 - 26-01-2025](#v0131-26-01-2025)
- [v0.12.3 - 22-01-2025](#v0123-22-01-2025)
- [v0.12.2 - 22-01-2025](#v0122-22-01-2025)
- [v0.12.1 - 05-01-2025](#v0121-05-01-2025)
- [v0.12.0 - 04-01-2025](#v0120-04-01-2025)
- [v0.11.0 - 03-01-2025](#v0110-03-01-2025)
- [v0.10.0 - 29-12-2024](#v0100-29-12-2024)
- [v0.9.2 - 28-12-2024](#v092-28-12-2024)
- [v0.9.1 - 27-12-2024](#v091-27-12-2024)
- [v0.9.0 - 27-12-2024](#v090-27-12-2024)
- [v0.8.0 - 26-12-2024](#v080-26-12-2024)
- [v0.7.0 - 22-12-2024](#v070-22-12-2024)
- [v0.6.1 - 21-12-2024](#v061-21-12-2024)
- [v0.6.0 - 21-12-2024](#v060-21-12-2024)
- [v0.5.0 - 20-12-2024](#v050-20-12-2024)

## v0.18.0 (Current) - *02-12-2025* {#v0180-current-02-12-2025}

### Brief Description (v0.18.0)

Feature release including updates to the `eza` command support, fixes for AI client connection messages and git error normalization, along with significant refactoring of AI utilities and enhanced test coverage.

### New Features in v0.18.0

- **Enhanced**: Update `eza` command to accept file pattern

### Bug Fixes in v0.18.0

- **Fixed**: Update AI client connection message and enhance git operations compatibility
  - **Issue**: AI client connection message was not clear or compatible.
  - **Root Cause**: Inconsistent message formatting.
  - **Solution**: Updated message and compatibility.
- **Fixed**: Normalize git error message patterns for case-insensitive matching
  - **Issue**: Git error messages were not being matched correctly.
  - **Root Cause**: Case sensitivity in regex.
  - **Solution**: Added case-insensitive matching.
- **Fixed**: Restore `-a .` functionality to select all files without interactive prompt
  - **Issue**: Using `-a .` still triggered the interactive file selection menu.
  - **Root Cause**: Workflow logic ignored CLI-provided files if they resolved to `.` (current directory) in a specific check.
  - **Solution**: Explicitly check if files were provided via CLI to bypass interactive selection.

### Improvements in v0.18.0

- **Code Quality**: Complete codebase reformatting to strict Ruff standards (as defined in `pyproject.toml`), enforcing consistency and modern Python practices.
- **UX**: Clarify file selection interaction instructions, replacing confusing toggle/invert help text with explicit navigation guidance and aligning the `-a .` flag with the interactive **All files** option by listing each staged file.
- **Improved**: Enhance `AIClient` with dependency injection support, enabling better testability and increasing code coverage from ~70% to 97%.
- **Improved**: Enhance `GitWorkflow` with dependency injection and add extensive test cases for better error handling and flow control, contributing to the significant coverage boost.
- **Refactored**: AI utilities and improve error handling
- **Refactored**: Git operations in git-acp
- **Documentation**: Update project overview with architecture diagrams and design patterns
- **Documentation**: Add comprehensive coding standards (AGENTS.md)

### Key Commits in v0.18.0

`663b42e`, `1950266`, `4e77245`, `a59aaa3`, `cde5617`, `73acc5e`,
`c3db738`

---

## v0.17.0 - *10-08-2025* {#v0170-10-08-2025}

### Brief Description (v0.17.0)

Minor feature release with refactors. Introduces a configurable fallback Ollama server and flattens the Git operations structure for maintainability. Includes test additions.

### New Features in v0.17.0

- Added: Configurable fallback Ollama server

### Improvements in v0.17.0

- Refactor: Flattened Git operations package structure
- Refactor: Internal cleanups across Git helpers
- Tests: Added basic to-do test scaffold

### Key Commits in v0.17.0

`f14f674`, `35960dd`, `3102ffb`, `57a2633`

---

## v0.16.0 - *August 2025* {#v0160-august-2025}

### Brief Description (v0.16.0)

Refactors across AI and Git helpers, dependency updates, and general enhancements.

### New Features in v0.16.0 (if any)

- Enhanced project structure and CLI improvements.

### Bug Fixes in v0.16.0 (if any)

- Fixed: Improve CLI add-path handling and enhance tests.
  - Issue: Incorrect handling of the -a flag paths in certain cases.
  - Root Cause: Argument parsing and path normalization edge cases.
  - Solution: Adjusted CLI option parsing and added tests.

### Improvements in v0.16.0 (if any)

- Refactor: Apply review fixes to AI and Git helpers.
- Refactor: AI client cleanup and dependency updates.

### Key Commits in v0.16.0

`778e045`, `bc6cbeb`, `08304d4`, `2990555`, `01a0ec3`

---

## v0.15.1 - *June 2025* {#v0151-june-2025}

### Summary (v0.15.1)

Major release introducing `pyproject.toml`, enhanced test coverage, project overview documentation, and improved CLI usability with glob pattern support for the `-a` flag.

### New Features in v0.15.1

- Added `pyproject.toml` for modern Python packaging and build system configuration
- Added project overview documentation for developers
- Enhanced `-a` flag to support glob patterns and multiple files
- Improved test coverage for branch creation, tag management, and protected branch deletion

### Improvements in v0.15.1

- Refactored CLI for improved usability
- Refactored imports and updated formatting functions
- Refactored AI client initialization and context gathering
- Refactored configuration constants and AI settings
- Updated `.gitignore` for better project structure

### Bug Fixes in v0.15.1

- Fixed CLI add-path handling edge cases

### Commits in v0.15.1

`ab20572`, `2867f4f`, `11f82ce`, `7fae0d1`, `44de6f1`, `3f7b6d4`

---

## v0.15.0 - *01-02-2025* {#v0150-01-02-2025}

### Summary (v0.15.0)

Major architectural refactor introducing modular package structure with separate modules for Git operations (history, remote, stash, status, tags), configuration management, and AI commit generation.

### New Features in v0.15.0

- Added Git history and diff analysis module
- Added remote management module
- Added stash operations module
- Added status tracking module
- Added configuration loader and settings modules
- Added CLI-specific formatting helpers and helper functions
- Added cancellation support for AI requests

### Improvements in v0.15.0

- Refactored CLI imports with new formatting and helper functions
- Refactored AI commit message generation to use new client and prompts
- Added main CLI entry point for cleaner execution
- Comprehensive documentation updates including CHANGELOG and test docs

### Commits in v0.15.0

`ff31124`, `a52f1f8`, `6b7ed52`, `4bd8052`, `c10535e`, `456e9be`, `f25958f`

---

## v0.14.2 - *09-06-2025* {#v0142-09-06-2025}

### Summary (v0.14.2)

Patch release with documentation improvements and minor fixes.

### Improvements in v0.14.2

- Updated API documentation
- Added comprehensive CHANGELOG.md
- Improved README clarity and structure

### Commits in v0.14.2

`b8d73f8`, `d26b0fb`

---

## v0.14.1 - *28-01-2025* {#v0141-28-01-2025}

### Summary (v0.14.1)

Major documentation and testing release with comprehensive test suites, detailed installation guides, and example GIFs.

### New Features in v0.14.1

- Added comprehensive test suite for formatting utilities, type definitions, and configuration
- Added commit type classification tests
- Added AI-powered commit message generation tests
- Added configuration management module
- Added example GIFs demonstrating default and simple output modes

### Improvements in v0.14.1

- Added detailed installation and usage guides
- Enhanced package documentation with detailed features
- Added comprehensive API overview and advanced usage documentation
- Updated `.gitignore` for better file exclusion

### Commits in v0.14.1

`7207751`, `23f6b14`, `0b88a5a`, `39abbfa`, `93ab634`, `43ea608`, `42d489e`

---

## v0.14.0 - *27-01-2025* {#v0140-27-01-2025}

### Summary (v0.14.0)

Feature release with enhanced CLI options, advanced prompt types for commit message generation, and improved signal handling.

### New Features in v0.14.0

- Enhanced commit message generation with advanced prompt type
- Refactored CLI options for better usability
- Added simple prompt type configuration option

### Improvements in v0.14.0

- Refactored package structure with new utility functions
- Enhanced AI client request handling for better progress tracking
- Improved signal handling for better user experience

### Bug Fixes in v0.14.0

- Fixed author metadata in setup.py

### Commits in v0.14.0

`87fad79`, `d515d58`, `e217f1c`, `3df752d`, `ff3ea1c`, `18e2488`

---

## v0.13.4 - *26-01-2025* {#v0134-26-01-2025}

### Summary (v0.13.4)

Refactoring release with improved code quality, enhanced AI client, and comprehensive documentation for environment variables and configuration options.

### Improvements in v0.13.4

- Enhanced AI client initialization and error handling
- Refactored `GitConfig` to a class structure
- Updated type annotations in constants.py
- Refactored imports in cli.py and classification.py
- Improved README formatting and examples
- Refactored `ai_utils.py` for better readability and maintainability
- Added detailed documentation for environment variables, AI/Git configuration, and commit types

### Commits in v0.13.4

`8ca5971`, `f0e127e`, `e2f1951`, `82a0251`, `5d371ca`, `484e292`, `4bbefc9`

---

## v0.13.3 - *26-01-2025* {#v0133-26-01-2025}

### Summary (v0.13.3)

Patch release with refactored recent commits retrieval and analysis.

### Improvements in v0.13.3

- Refactored recent commits retrieval and analysis in git_acp

### Commits in v0.13.3

`5874d8e`, `b8626b6`

---

## v0.13.2 - *26-01-2025* {#v0132-26-01-2025}

### Summary (v0.13.2)

Patch release adding timeout configuration for AI requests.

### New Features in v0.13.2

- Added timeout configuration for AI requests in `.env.example`

### Commits in v0.13.2

`fbd9025`, `7136d69`

---

## v0.13.1 - *26-01-2025* {#v0131-26-01-2025}

### Summary (v0.13.1)

Feature release with interactive AI-generated commit message editing and enhanced AI support.

### New Features in v0.13.1

- Added interactive option to allow AI-generated commit messages
- Enhanced commit message generation with AI support
- Added AI message formatting colors to constants.py
- Added AI temperature settings configuration

### Improvements in v0.13.1

- Refactored type hints and improved code readability
- Added new type definitions for git-acp package
- Added utility functions for staged/unstaged changes, branch management, and remote operations

### Bug Fixes in v0.13.1

- Enhanced commit message debugging in ai_utils.py

### Commits in v0.13.1

`86906a4`, `a65447c`, `b19d949`, `d41b7a5`, `eedbd88`, `6b89a8d`, `6b1456f`, `7ad77a5`

---

## v0.12.3 - *22-01-2025* {#v0123-22-01-2025}

### Summary (v0.12.3)

Patch release with auto-selecting suggested commit type feature.

### New Features in v0.12.3

- Added auto-selecting of suggested commit type in CLI

### Commits in v0.12.3

`ae7c13b`, `fe1ff06`

---

## v0.12.2 - *22-01-2025* {#v0122-22-01-2025}

### Summary (v0.12.2)

Feature release with advanced commit message generation options and improved file selection.

### New Features in v0.12.2

- Added advanced prompt type setting
- Added default prompt type configuration in constants.py
- Enhanced commit message generation with advanced options
- Updated commit type definitions

### Improvements in v0.12.2

- Refactored environment variables and added terminal configuration

### Bug Fixes in v0.12.2

- Enhanced file selection with user feedback
- Fixed file selection and command execution issues

### Commits in v0.12.2

`fdb42f4`, `a009ae4`, `ee9b5ac`, `750a38b`, `6f416e2`, `db6e518`, `fbc05d1`, `2501bc2`

---

## v0.12.1 - *05-01-2025* {#v0121-05-01-2025}

### Summary (v0.12.1)

Patch release updating dependencies for click, rich, questionary, openai, and python-dotenv.

### Improvements in v0.12.1

- Updated requirements with specific versions for click, rich, questionary, openai, and python-dotenv

### Commits in v0.12.1

`6b87501`

---

## v0.12.0 - *04-01-2025* {#v0120-04-01-2025}

### Summary (v0.12.0)

Feature release with enhanced AI integration and `.env.example` configuration file.

### New Features in v0.12.0

- Added `.env.example` file for AI configuration settings
- Enhanced AI integration for improved commit message generation

### Improvements in v0.12.0

- Enhanced README with modern badges and detailed features
- Updated `.gitignore` to exclude `.env.example`

### Commits in v0.12.0

`be1c833`, `cfc5e7f`, `29bd504`, `ba2ca01`, `83fb666`

---

## v0.11.0 - *03-01-2025* {#v0110-03-01-2025}

### Summary (v0.11.0)

Feature release with improved commit type selection highlighting and enhanced AI integration.

### New Features in v0.11.0

- Refactored constants.py for better maintainability
- Enhanced AI integration for commit message generation

### Improvements in v0.11.0

- Optimized commit type selection with AI-generated messages
- Enhanced commit type selection with suggested highlight
- Refactored commit message generation with detailed context
- Improved debug functions and error handling
- Updated setup.py with new dependencies and constraints

### Commits in v0.11.0

`0e9e935`, `b19a304`, `5872e0b`, `0878a65`, `f2294a0`, `34075e8`, `74b3b62`, `de2df4a`

---

## v0.10.0 - *29-12-2024* {#v0100-29-12-2024}

### Summary (v0.10.0)

Major feature release with test suite, Ollama support, enhanced commit filtering, and verbose output.

### New Features in v0.10.0

- Added Ollama to requirements for local AI model support
- Added test suite for git operations and system prompt generation
- Added AI utilities test suite
- Enhanced commit message generation with related commits filtering
- Added verbose output for git command execution

### Improvements in v0.10.0

- Refactored commit message generation to use AI model
- Enhanced AI utilities and formatting
- Improved error handling with generic exception handling
- Added `.gitignore` for tests directory
- Added typing and tqdm to requirements

### Bug Fixes in v0.10.0

- Fixed entry point for git-acp script
- Simplified status handling in `get_changed_files`

### Commits in v0.10.0

`4b07e3f`, `4cb6dca`, `3a096ca`, `5c87277`, `f54db60`, `63bb88c`, `f791f3e`, `031ec02`

---

## v0.9.2 - *28-12-2024* {#v092-28-12-2024}

### Summary (v0.9.2)

Patch release with enhanced commit message generation and context analysis.

### New Features in v0.9.2

- Enhanced commit message generation with context analysis
- Added new functions for commit analysis in git_acp package

### Commits in v0.9.2

`f9f0b5d`, `87af1cd`, `7d0337f`

---

## v0.9.1 - *27-12-2024* {#v091-27-12-2024}

### Summary (v0.9.1)

Patch release with simplified status handling.

### Bug Fixes in v0.9.1

- Simplified status handling in `get_changed_files`

### Commits in v0.9.1

`286b285`, `f446f78`

---

## v0.9.0 - *27-12-2024* {#v090-27-12-2024}

### Summary (v0.9.0)

Major architectural refactor introducing modular package structure with separate modules for git operations, AI utilities, and commit classification.

### New Features in v0.9.0

- Added git operations module for git-acp
- Added commit type classification module
- Added AI utilities module
- Enhanced git-acp with advanced features
- Updated main entry point for cleaner execution

### Improvements in v0.9.0

- Refactored codebase into modular structure
- Updated package documentation

### Commits in v0.9.0

`c1db272`, `b0639bf`, `1a41686`, `e978a8b`, `13d21c0`, `38468ac`, `f293468`, `f339f35`

---

## v0.8.0 - *26-12-2024* {#v080-26-12-2024}

### Summary (v0.8.0)

Feature release with improved handling of staged and unstaged changes.

### Bug Fixes in v0.8.0

- Enhanced git_acp to handle staged and unstaged changes properly

### Commits in v0.8.0

`06c3d64`, `2d44168`

---

## v0.7.0 - *22-12-2024* {#v070-22-12-2024}

### Summary (v0.7.0)

Feature release with improved commit type selection and user interrupt handling.

### New Features in v0.7.0

- Adjusted commit type selection with suggested tag and validation
- Added user interrupt handling (Ctrl+C)

### Improvements in v0.7.0

- Updated installation instructions
- Updated command name and references in README

### Commits in v0.7.0

`f1658fb`, `960970c`, `8e60553`, `36ca782`, `90e5c08`

---

## v0.6.1 - *21-12-2024* {#v061-21-12-2024}

### Summary (v0.6.1)

Patch release for version consistency across project files.

### Commits in v0.6.1

`b59b0e5`

---

## v0.6.0 - *21-12-2024* {#v060-21-12-2024}

### Summary (v0.6.0)

Major feature release introducing interactive commit type selection, verbose mode, and questionary-based UI.

### New Features in v0.6.0

- Added interactive commit type selection using questionary
- Added verbose mode to GitConfig
- Added `.gitignore` for default file exclusions
- Enhanced file selection with improved error handling
- Added questionary dependency for interactive prompts

### Improvements in v0.6.0

- Enhanced README with versioning and detailed installation instructions
- Added main entry point for git-acp package

### Bug Fixes in v0.6.0

- Enhanced file selection logic

### Commits in v0.6.0

`ac72c83`, `87cfc1e`, `f797e17`, `bda2482`, `a8bbeca`, `c0448a1`, `0347c08`, `af44e11`, `45cc4e3`, `21df196`, `a67d6e7`, `28e2264`

---

## v0.5.0 - *20-12-2024* {#v050-20-12-2024}

### Summary (v0.5.0)

Initial packaging release with `setup.py` for PyPI distribution.

### New Features in v0.5.0

- Added `setup.py` for package installation and distribution
- Defined project metadata (name, version, author, description)
- Added console scripts entry point for CLI execution
- Specified required dependencies (click, rich, typing)

### Commits in v0.5.0

`3719ddc`

---
