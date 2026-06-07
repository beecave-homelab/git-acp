# VERSIONS.md

## Table of Contents

- [v0.26.0 (Current) - 07-06-2026](#v0260-current---07-06-2026)
- [v0.25.0 - 04-06-2026](#v0250---04-06-2026)
- [v0.24.0 - 24-05-2026](#v0240---24-05-2026)
- [v0.23.0 - 27-01-2026](#v0230---27-01-2026)
- [v0.22.0 - 13-01-2026](#v0220---13-01-2026)
- [v0.20.0 - 20-12-2025](#v0200---20-12-2025)
- [v0.19.0 - 19-12-2025](#v0190---19-12-2025)
- [v0.18.0 - 02-12-2025](#v0180---02-12-2025)
- [v0.17.0 - 10-08-2025](#v0170---10-08-2025)
- [v0.16.0 - 08-08-2025](#v0160---08-08-2025)
- [v0.15.1 - 20-06-2025](#v0151---20-06-2025)
- [v0.15.0 - 01-02-2025](#v0150---01-02-2025)
- [v0.14.2 - 09-06-2025](#v0142---09-06-2025)
- [v0.14.1 - 30-11-2025](#v0141---30-11-2025)
- [v0.14.0 - 27-01-2025](#v0140---27-01-2025)
- [v0.13.4 - 26-01-2025](#v0134---26-01-2025)
- [v0.13.3 - 26-01-2025](#v0133---26-01-2025)
- [v0.13.2 - 26-01-2025](#v0132---26-01-2025)
- [v0.13.1 - 26-01-2025](#v0131---26-01-2025)
- [v0.12.3 - 22-01-2025](#v0123---22-01-2025)
- [v0.12.2 - 22-01-2025](#v0122---22-01-2025)
- [v0.12.1 - 05-01-2025](#v0121---05-01-2025)
- [v0.12.0 - 04-01-2025](#v0120---04-01-2025)
- [v0.11.0 - 03-01-2025](#v0110---03-01-2025)
- [v0.10.0 - 29-12-2024](#v0100---29-12-2024)
- [v0.9.2 - 28-12-2024](#v092---28-12-2024)
- [v0.9.1 - 27-12-2024](#v091---27-12-2024)
- [v0.9.0 - 27-12-2024](#v090---27-12-2024)
- [v0.8.0 - 26-12-2024](#v080---26-12-2024)
- [v0.7.0 - 22-12-2024](#v070---22-12-2024)
- [v0.6.1 - 21-12-2024](#v061---21-12-2024)
- [v0.6.0 - 21-12-2024](#v060---21-12-2024)
- [v0.5.0 - 20-12-2024](#v050---20-12-2024)

## v0.26.0 (Current) - *07-06-2026*

### ✨ **Add weighted scoring classifier and expanded commit type detection**

### ✨ New Features in v0.26.0

- **Added**: Weighted scoring classifier for smarter Conventional Commit type recommendations.
- **Added**: Analysis infrastructure and data structures for scoring-based classification.
- **Added**: File classifier support for path-aware commit type scoring.
- **Added**: Build, CI, and performance commit type detection.

### 🔧 Improvements in v0.26.0

- **Refactored**: Classification module to support scoring-driven recommendations.
- **Updated**: CLI and Git exports to integrate the expanded classifier behavior.
- **Updated**: Formatting in classification modules and tests.

### 🧪 Testing improvements in v0.26.0

- **Added**: Regression tests for the scoring classifier.
- **Added**: Auto-detection coverage for build, CI, and performance commit types.
- **Added**: Workflow assertions for `unstage_files` behavior.

### 📝 Key Commits in v0.26.0

`e254c53`, `4e71e38`, `5d4999b`, `124f403`, `1e3f710`, `5dc86ec`, `2143234`, `e545046`, `16089d4`

---

## v0.25.0 - *04-06-2026*

### ✨ **Add --setup flag to automate initial config creation**

### ✨ New Features in v0.25.0

- **Added**: `--setup` flag to the CLI to automate initial `.env` configuration creation.
- **Added**: `--force` flag alongside `--setup` to overwrite an existing `.env` file.
- **Added**: `run_setup()` function in `env_config.py` to programmatically generate `.env` files from a template.
- **Added**: `git_acp/.env.example` as a comprehensive template for all supported environment variables.

### 🔧 Improvements in v0.25.0

- **Refactored**: `scripts/setup-config.py` simplified to a thin wrapper around `run_setup()`.
- **Updated**: `git_acp/config/__init__.py` to re-export `run_setup` for public access.

### 🐛 Bug Fixes in v0.25.0

- **Fixed**: Synchronized `.env.example` content with `env_config.py` defaults after CodeRabbit review.

### 🧪 Testing improvements in v0.25.0

- **Added**: CLI tests for `--setup` and `--force` flag behavior.
- **Added**: Unit tests for `run_setup()` including overwrite logic and template rendering.

### 📝 Key Commits in v0.25.0

`cc46eb9`, `db2ac21`, `55de509`, `5a74d2c`, `ec96931`, `e4bbac6`, `8e343ab`

---

## v0.24.0 - *24-05-2026*

### ✨ Brief Description (v0.24.0)

Feature release adding emoji-aware prefix stripping, scoped file filtering with `Path.match`, auto-group mode, dry-run support, mypy type checking, and numerous bug fixes across AI utilities, classification, and commit message handling.

### ✨ New Features in v0.24.0

- **Added**: Emoji-aware conventional commit prefix stripping with optional leading emoji support.
- **Added**: Scoped `-a` filtering using `Path.match` with `**/` glob support and relative-path handling.
- **Added**: Auto-group mode (`-ag/--auto-group`) for deterministic multi-commit workflow.
- **Added**: `--dry-run` flag for testing the complete workflow without committing or pushing.
- **Added**: Mypy type checking integration in local CI script and `pyproject.toml`.
- **Added**: Type annotations using union syntax across CLI, AI, and config modules.
- **Added**: CodeRabbit configuration file for automated code review.
- **Added**: Dependency installation and auto-install support in local CI script.
- **Added**: PR validation workflow for CI.
- **Added**: Configurable fallback Ollama server.
- **Added**: Local CI script for CI pipeline.
- **Added**: `--version` flag to display the current version and exit.
- **Added**: Context management functions for AI prompt optimization including token estimation and context budget calculation.

### 🐛 Bug Fixes in v0.24.0

- **Fixed**: Move `shlex` and `get_changed_files` imports to top of module.
- **Fixed**: Add error handling for malformed `config.files` value.
- **Fixed**: Include untracked file diffs in AI commit context.
- **Fixed**: Enhanced commit type validation with case-insensitive and prefix matching support.
- **Fixed**: Add regex support to `ai_utils.py` for cleaning AI-generated commit messages.
- **Fixed**: Update file filter logic to handle special characters correctly.
- **Fixed**: Fix file filter normalization in `file_filter.py`.
- **Fixed**: Add scoped file filtering and scope-aware commit context.
- **Fixed**: Scope file selection and skip staging in dry run.
- **Fixed**: Remove spacy dependency group from PR CI workflow.
- **Fixed**: Update `--dry-run` flag syntax in `VERSIONS.md` and `workflow.py`.
- **Fixed**: Enhance `exa-codebase-tree.sh` with error handling and default target path.
- **Fixed**: Update Ollama model pull command in `AIClient` and add verbose note in `GitWorkflow`.
- **Fixed**: Refine commit classification logic for majority files match.
- **Fixed**: Enhance file path pattern matching in `classification.py`.
- **Fixed**: Enhance `.env` file exclusion in `diff.py` and update `types.py`.
- **Fixed**: Add manual commit message prompt to interaction.
- **Fixed**: Update commit message formatting and context.
- **Fixed**: Normalize git error message patterns for case-insensitive matching.
- **Fixed**: Update AI client connection message and enhance git operations compatibility.

### 🔧 Improvements in v0.24.0

- **Refactored**: Clean up imports and simplify prefix stripping logic.
- **Refactored**: Update CLI to remove scoped groups logic.
- **Refactored**: Enhance commit message generation with context management and token estimation.
- **Refactored**: Refactor manual commit message prompt in `GitWorkflow`.
- **Refactored**: Refactor file selection logic in interaction and workflow.
- **Refactored**: Enhance `AIClient` with dependency injection support and test coverage.
- **Refactored**: Enhance `GitWorkflow` and add test cases for better error handling.
- **Refactored**: Flatten git operations package structure.
- **Refactored**: Apply review fixes to AI and git helpers.
- **Refactored**: Refactor AI client and update dependencies.
- **Improved**: Code formatting and line length compliance across AI utilities.
- **Improved**: Configuration system with context ratio settings for different prompt types.

### 🧪 Testing improvements in v0.24.0

- **Added**: Test for emoji-leading prefixes in prefix stripping.
- **Added**: Test to prevent pytest from collecting `TestInteraction` class.
- **Added**: Test case for `--version` flag in CLI.
- **Added**: Test case for dry-run with verbose logging in git add.
- **Added**: Tests for auto-grouping behavior and commit message semantics.
- **Added**: Tests for dry-run behavior and file filtering.
- **Added**: Type annotations and casts to fix mypy type checking errors in tests.
- **Added**: Commit type classification mocks across multiple test files.
- **Enhanced**: Test coverage for AI utilities, CLI, configuration, git operations, and commit analysis.

### 📝 Key Commits in v0.24.0

`34aae78`, `6771a13`, `2993717`, `99ac59c`, `8703bce`, `7ed58a1`, `53618ca`, `dc8dc10`, `c81a7a3`, `009204d`

---

## v0.23.0 - *27-01-2026*

### ✨ Brief Description (v0.23.0)

Feature release adding `--version` flag to display the current version and exit.

### ✨ New Features in v0.23.0

- **Added**: `--version` flag to display the current version and exit.

### 🐛 Bug Fixes in v0.23.0

None.

### 🔧 Improvements in v0.23.0

- **Documentation**: Updated project overview with new version information.
- **Documentation**: Updated AGENTS.md with rule about importing from single source of truth.

### 🧪 Testing improvements in v0.23.0

- **Added**: Test for `--version` flag to verify correct version display.

### 📝 Key Commits in v0.23.0

`c81a7a3`, `dc07d1d`

---

## v0.22.0 - *13-01-2026*

### ✨ Brief Description (v0.22.0)

Feature release adding scoped file selection and filtering for commit message generation and `--dry-run`, including robust glob matching with `**/` support and relative-path handling.

### ✨ New Features in v0.22.0

- **Added**: Scoped file selection and filtering support for commit message context.
- **Added**: Glob filtering improvements using `pathlib.Path.match`, including `**/` support and relative path handling.

### 🐛 Bug Fixes in v0.22.0

- **Fixed**: Commit message file list filtering to respect scope selection.
- **Fixed**: Remove unused commit prompt helper.

### 🔧 Improvements in v0.22.0

- **Refactored**: Centralize file scope filtering logic.
- **Refactored**: File scope handling in `GitWorkflow`.

### 🧪 Testing improvements in v0.22.0

- **Added**: Tests for dry-run behavior and file filtering.
- **Added**: Test coverage for auto-group with `-a` glob pattern filters.

### 📝 Key Commits in v0.22.0

`07dba87`, `83f0bc5`, `893e969`, `5ded0b4`, `2509ef8`, `1d8c5f2`, `3c07f0c`

---

## v0.21.0 - *27-12-2025*

### ✨ Brief Description (v0.21.0)

Feature release adding auto-group mode to split unstaged changes into multiple focused commits using deterministic file grouping.

### ✨ New Features in v0.21.0

- **Added**: `--auto-group` flag (`-ag, --auto-group`) to group unstaged changes into multiple focused commits.
- **Added**: Deterministic file grouping via `group_changed_files()`.
- **Added**: Default configuration to cap the number of non-commit-type groups.

### 🐛 Bug Fixes in v0.21.0

- **Fixed**: Commit type metadata and descriptions used for classification and display.

### 🔧 Improvements in v0.21.0

- **Improved**: Multi-commit orchestration flow and state isolation across repeated workflow runs.
- **Refactored**: Output formatting and debug handling for better readability.

### 🧪 Testing improvements in v0.21.0

- **Added**: Tests covering auto-grouping behavior and commit message semantics.

### 📝 Key Commits in v0.21.0

`aa6be1b`, `ae43d81`, `9951b5e`, `b742af5`, `12d004f`

---

## v0.20.0 - *20-12-2025*

### ✨ Brief Description (v0.20.0)

Feature release adding --dry-run flag functionality for testing the complete git-acp workflow without actually committing or pushing changes.

### ✨ New Features in v0.20.0

- **Added**: `--dry-run` flag (`-dr, --dry-run`) to show what would be committed without actually committing or pushing.
- **Added**: Context management functions for AI prompt optimization including token estimation and context budget calculation.
- **Added**: Structured prompt templates for both simple and advanced AI commit message generation.

### 🔧 Improvements in v0.20.0

- **Enhanced**: AI commit message generation with better context window management and token optimization.
- **Improved**: Code formatting and line length compliance across AI utilities.
- **Updated**: Configuration system with context ratio settings for different prompt types.

### ⚠️ Migration Notes in v0.20.0

- **CLI flag change**: `-m` now maps to `--model` (AI model override). If you previously used `-m` for a manual commit message, use `-mb/--message-body` instead.

### 🧪 Testing improvements in v0.20.0

- **Added**: Comprehensive test coverage for context management functions including token estimation and truncation.
- **Updated**: Test serialization to include new dry_run configuration field.

### 📝 Key Commits in v0.20.0

`53618ca`, `b2015bb`, `194ad44`, `51090ed`, `8be2b5e`

---

## v0.19.0 - *19-12-2025*

### ✨ Brief Description (v0.19.0)

Feature release improving commit type recommendations by prioritizing file-path heuristics and correctly parsing the repository's emoji-style conventional commit prefixes.

### ✨ New Features in v0.19.0

- **Added**: `FILE_PATH_PATTERNS` classification rules to reliably infer commit types from changed file paths.
- **Enhanced**: Commit type classification priority order to prefer message prefix, then file paths, then keyword fallbacks.

### 🔧 Improvements in v0.19.0

- **Improved**: Commit message prefix parsing to support repo-style prefixes such as `feat ✨:` and `fix 🐛:` (including optional scopes).
- **Improved**: User interaction commit type selection flow to accept and display the generated/edited commit message context.

### 🧪 Testing improvements in v0.19.0

- **Updated**: Classification test coverage to validate file-path-first behavior and emoji-style prefix parsing.

### 📝 Key Commits in v0.19.0

`1e591db`, `928d382`, `6e60688`, `867861c`, `9982df8`

---

## v0.18.0 - *02-12-2025*

### Brief Description (v0.18.0)

Feature release including updates to the `eza` command support, fixes for AI client connection messages and git error normalization, along with significant refactoring of AI utilities and enhanced test coverage.

### New Features in v0.18.0

- **Enhanced**: Update `eza` command to accept file pattern
- **Added**: `scripts/local-ci.sh` convenience script to run the local CI pipeline (`pdm run fix`, `pdm run format`, `pdm run test`, `pdm run test-cov`) with a single command, including help text and optional log file output.

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
- **Fixed**: Ensure `-a <pattern>` lists only files matching the resolved CLI targets
  - **Issue**: Using patterns such as `-a "tests/"` caused the CLI to list all changed files in the repository instead of only those under `tests/`.
  - **Root Cause**: The workflow printed every changed file discovered by `get_changed_files` without respecting the resolved `-a` targets.
  - **Solution**: Updated `GitWorkflow` to filter the "Adding files:" list to only those paths affected by the resolved `-a` patterns, while preserving the `-a .` behavior of listing all changed files.
- **Fixed**: Ensure manual commit fallback after AI failures prompts for and preserves a user-provided message, and cleanly unstages files when exiting without a message.
  - **Issue**: After AI commit message generation failures, the workflow could abort even when the user opted into a manual message, or leave staged changes behind when no message was ultimately provided.
  - **Root Cause**: Commit message handling logic did not consistently prompt for a manual message or unstage files across all fallback paths.
  - **Solution**: Introduced a dedicated `_prompt_manual_message` helper in `GitWorkflow` and updated the commit message flow to always prompt once and unstage on missing messages.

### Improvements in v0.18.0

- **Code Quality**: Complete codebase reformatting to strict Ruff standards (as defined in `pyproject.toml`), enforcing consistency and modern Python practices.
- **UX**: Clarify file selection interaction instructions, replacing confusing toggle/invert help text with explicit navigation guidance and aligning the `-a .` flag with the interactive **All files** option by listing each staged file.
- **Improved**: Enhance `AIClient` with dependency injection support, enabling better testability and increasing code coverage from ~70% to 97%.
- **Improved**: Enhance `GitWorkflow` with dependency injection and add extensive test cases for better error handling and flow control, contributing to the significant coverage boost.
- **Refactored**: AI utilities and improve error handling
- **Refactored**: Git operations in git-acp
- **Refactored**: File selection UX in `RichQuestionaryInteraction` and `GitWorkflow` to better align CLI `-a` usage with interactive "All files" behavior.
- **Documentation**: Update project overview with architecture diagrams and design patterns
- **Documentation**: Add comprehensive coding standards (AGENTS.md)
- **UX**: Improve `GitWorkflow` commit message handling by centralizing manual message prompting and ensuring staged changes are always unstaged when exiting without a commit message, reducing surprising exits after AI failures.

### Key Commits in v0.18.0

`663b42e`, `1950266`, `4e77245`, `a59aaa3`, `cde5617`, `73acc5e`,
`c3db738`

---

## v0.17.0 - *10-08-2025*

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

## v0.16.0 - *08-08-2025*

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

## v0.15.1 - *20-06-2025*

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

## v0.15.0 - *01-02-2025*

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

## v0.14.2 - *09-06-2025*

### Summary (v0.14.2)

Patch release with documentation improvements and minor fixes.

### Improvements in v0.14.2

- Updated API documentation
- Added comprehensive CHANGELOG.md
- Improved README clarity and structure

### Commits in v0.14.2

`b8d73f8`, `d26b0fb`

---

## v0.14.1 - *30-11-2025*

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

## v0.14.0 - *27-01-2025*

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

## v0.13.4 - *26-01-2025*

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

## v0.13.3 - *26-01-2025*

### Summary (v0.13.3)

Patch release with refactored recent commits retrieval and analysis.

### Improvements in v0.13.3

- Refactored recent commits retrieval and analysis in git_acp

### Commits in v0.13.3

`5874d8e`, `b8626b6`

---

## v0.13.2 - *26-01-2025*

### Summary (v0.13.2)

Patch release adding timeout configuration for AI requests.

### New Features in v0.13.2

- Added timeout configuration for AI requests in `.env.example`

### Commits in v0.13.2

`fbd9025`, `7136d69`

---

## v0.13.1 - *26-01-2025*

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

## v0.12.3 - *22-01-2025*

### Summary (v0.12.3)

Patch release with auto-selecting suggested commit type feature.

### New Features in v0.12.3

- Added auto-selecting of suggested commit type in CLI

### Commits in v0.12.3

`ae7c13b`, `fe1ff06`

---

## v0.12.2 - *22-01-2025*

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

## v0.12.1 - *05-01-2025*

### Summary (v0.12.1)

Patch release updating dependencies for click, rich, questionary, openai, and python-dotenv.

### Improvements in v0.12.1

- Updated requirements with specific versions for click, rich, questionary, openai, and python-dotenv

### Commits in v0.12.1

`6b87501`

---

## v0.12.0 - *04-01-2025*

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

## v0.11.0 - *03-01-2025*

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

## v0.10.0 - *29-12-2024*

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

## v0.9.2 - *28-12-2024*

### Summary (v0.9.2)

Patch release with enhanced commit message generation and context analysis.

### New Features in v0.9.2

- Enhanced commit message generation with context analysis
- Added new functions for commit analysis in git_acp package

### Commits in v0.9.2

`f9f0b5d`, `87af1cd`, `7d0337f`

---

## v0.9.1 - *27-12-2024*

### Summary (v0.9.1)

Patch release with simplified status handling.

### Bug Fixes in v0.9.1

- Simplified status handling in `get_changed_files`

### Commits in v0.9.1

`286b285`, `f446f78`

---

## v0.9.0 - *27-12-2024*

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

## v0.8.0 - *26-12-2024*

### Summary (v0.8.0)

Feature release with improved handling of staged and unstaged changes.

### Bug Fixes in v0.8.0

- Enhanced git_acp to handle staged and unstaged changes properly

### Commits in v0.8.0

`06c3d64`, `2d44168`

---

## v0.7.0 - *22-12-2024*

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

## v0.6.1 - *21-12-2024*

### Summary (v0.6.1)

Patch release for version consistency across project files.

### Commits in v0.6.1

`b59b0e5`

---

## v0.6.0 - *21-12-2024*

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

## v0.5.0 - *20-12-2024*

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
