# Changelog

All notable changes to this project will be documented in this file.

## [0.14.2] - 30-01-2025

### Added
- test 🧪: Add unit tests for formatting utilities and type definitions (23f6b14)
- test 🧪: Add comprehensive test suite and commit type classification (0b88a5a)
- test 🧪: Add comprehensive test suite for configuration constants and environment handling (39abbfa)
- test 🧪: Add development requirements to requirements.dev.txt (6b923bc)

### Changed
- refactor ♻️: Add cancellation support for AI requests in AIClient (e77f260)
- docs 📝: Update test documentation and add error handling testing (8c95c20)
- docs 📝: Add comprehensive CHANGELOG.md and update versioning (63ceee3)
- docs 📝: Update README.md for improved clarity and structure (8b0daa1)
- chore 📦: Bump version to 0.14.2 in README, API documentation, and setup.py (d26b0fb)
- docs 📝: Generate detailed test cases for git_acp package (eaa6456)

### Fixed
- test 🧪: Remove deprecated test suite for git_acp/cli/cli.py (fd68c2a)

### Removed
- revert ⏪: Remove outdated test plan for `cli.py` (24e215a)
- chore 📦: Remove AI utilities and git operations test files (e05581f)

## [0.14.1] - 29-01-2025

### Added
- feat ✨: Add comprehensive test suite for git_acp package (93ab634)
- feat ✨: Add interactive mode for AI-generated commit messages (6b1456f)
- feat ✨: Add AI message formatting colors to constants.py (e2711e8)
- feat ✨: Add .env.example for AI configuration settings (ba2ca01)
- test 🧪: Add test suite for git operations and system prompt generation (63bb88c)
- test 🧪: Add AI utilities test suite and system prompt generation (f791f3e)
- test 🧪: Add tests package and refactor git_operations.py (80d5411)

### Changed
- docs 📝: Update version to 0.14.1 in documentation files (6baeb55)
- chore 📦: Bump version to 0.14.1 in README, init.py, and setup.py (7207751)
- docs 📝: Update README.md and documentation links (6901c36)
- chore 📦: Update .gitignore to exclude additional files and directories (50b53d9)
- docs 📝: Update installation and configuration instructions (66e5c82)
- docs 📝: Add tested models to advanced usage documentation (425a7bb)
- docs 📝: Refactor README.md for improved clarity and structure (eea8a1e)

### Fixed
- fix 🐛: Add configuration management for git-acp (e02019c)
- fix 🐛: Enhance user experience with signal handling in git_acp (d515d58)

## [0.14.0] - 28-01-2025

### Changed
- chore 📦: Bump version to 0.14.0 and update README and setup files (87fad79)
- chore 📦: Update .gitignore and enhance documentation files (3da94d0)
- chore 📦: Update .gitignore and add documentation files (1327678)
- chore 📦: Update .gitignore and add assets, enhance README (3c254a4)
- docs 📝: Update README with Ollama logo and enhance documentation (dfe5fbb)
- docs 📝: Update commit type descriptions in README (d939244)
- docs 📝: Update Ollama API endpoint in README with placeholder (a5cc1c7)

### Added
- feat ✨: Add .gitignore for tests and update git-ignore entries (7b28aad)
- feat ✨: Add ollama to requirements and update typing dependency (031ec02)

### Fixed
- fix 🐛: Update author name and remove email in setup.py (e3f0545)
- fix 🐛: Enhance AI client request handling for better progress tracking (18e2488)

## [0.13.4] - 27-01-2025

### Changed
- chore 📦: Update version to 0.13.4 and enhance documentation (8ca5971)
- perf 🚀: Enhance AI client initialization and error handling (8ca5971)

### Refactoring
- refactor ♻️: Enhance AI client initialization and error handling (f0e127e)
- refactor ♻️: Remove unused imports and update type imports in git_operations.py (82a0251)

## [0.13.3] - 26-01-2025

### Changed
- chore 📦: Bump version to 0.13.3 in README, init.py, and setup.py (5874d8e)
- refactor ♻️: Refactor recent commits retrieval and analysis in git_acp (b8626b6)

## [0.13.2] - 25-01-2025

### Changed
- chore 📦: Update version to 0.13.2 in README, init.py, and setup.py (fbd9025)
- feat ✨: Add timeout configuration for AI requests in .env.example (7136d69)

## [0.13.1] - 24-01-2025

### Changed
- chore 📦: Bump version to 0.13.1 in README, __init__.py, and setup.py (86906a4)
- chore 📦: Update version number and dependencies in README.md (4e14c97)

### Refactoring
- refactor ♻️: Refactor type hints and improve code readability (a65447c)

## [0.12.3] - 23-01-2025

### Changed
- chore 📦: Bump version to 0.12.3 and update dependencies (ae7c13b)

### Style
- style 💎: Add auto-selecting of suggested commit type in CLI (fe1ff06)

## [0.12.2] - 22-01-2025

### Changed
- chore 📦: Bump version to 0.12.2 across README.md, setup.py, and git_acp/__init__.py (fdb42f4)
- chore 📦: Update .env.example with advanced prompt type setting (ee9b5ac)

### Fixed
- fix 🐛: Enhance file selection with user feedback (a009ae4)

## [0.12.1] - 21-01-2025

### Changed
- chore 📦: Update version to 0.12.1 and add new requirements (6b87501)
- chore 📦: Update commit type definitions in .env.example and constants.py (2501bc2)

## [0.12.0] - 20-01-2025

### Changed
- chore 📦: Bump version to 0.12.0 and update README badges (be1c833)

### Documentation
- docs 📝: Enhance README with modern badges and detailed features (cfc5e7f)

## [0.11.0] - 19-01-2025

### Changed
- chore 📦: Update version to 0.11.0 in all files and README (0e9e935)

### Features
- feat ✨: Enhance commit message generation with AI model and verbose output (3a096ca)
- feat ✨: Refactor commit message generation to use AI model (22adb80)

## [0.10.0] - 18-01-2025

### Changed
- chore 📦: Update version to 0.10.0 in all relevant files (9674faa)
- chore 📦: Update setup.py with new dependencies and constraints (d057846)
- chore 📦: Update version to 0.10.0 in README, Python files and setup.py (4b07e3f)

### Added
- feat ✨: Add git operations module for git-acp (b0639bf)
- feat ✨: Add Git Add-Commit-Push automation tool (1a41686)

## [0.9.2] - 17-01-2025

### Changed
- chore 📦: Bump version to 0.9.2 in README, Python files (f9f0b5d)
- chore 📦: Update entry point for git-acp script (b235b52)

## [0.9.1] - 16-01-2025

### Fixed
- fix 🐛: Simplify status handling in get_changed_files (f446f78)

## [0.9.0] - 15-01-2025

### Changed
- chore 📦: Update version number to 0.9.0 in documentation and code (c1db272)
- chore 📦: Update main entry point for git-acp (38468ac)
- docs 📝: Update git_acp package documentation (f293468)

### Added
- feat ✨: Add commit type classification module for git-acp (e978a8b)
- feat ✨: Add AI utilities module for git-acp package (13d21c0)

## [0.8.0] - 14-01-2025

### Changed
- chore 📦: Bump version to 0.8.0 in README, git_acp.py, and setup.py (06c3d64)

### Fixed
- fix 🐛: Enhance git_acp to handle staged and unstaged changes (2d44168)

## [0.7.0] - 13-01-2025

### Changed
- chore 📦: Bump version to 0.7.0 in README, script, and setup file (f1658fb)
- docs 📝: Update installation instructions for git-acp (36ca782)
- docs 📝: Update command name and references in README (90e5c08)

### Added
- feat ✨: Add interactive commit type selection (bda2482)
- feat ✨: Add verbose mode to GitConfig and update functions (a8bbeca)

## [0.6.1] - 12-01-2025

### Changed
- chore 📦: Bump version to 0.6.1 in README, script, and setup.py (b59b0e5)

### Fixed
- fix 🐛: Enhance file selection logic in git_acp (ac72c83)

## [0.6.0] - 11-01-2025

### Changed
- chore 📦: Update version to 0.6.0 and correct date formatting (87cfc1e)
- feat ✨: Update Git-acp.sh to include commit type mappings and improve message formatting (8570c77)

### Added
- feat ✨: Add .gitignore to ignore default files (c0448a1)
- feat ✨: Add questionary to requirements.txt (af44e11)
- feat ✨: Add questionary to install_requires in setup.py (45cc4e3)
- feat ✨: Add git_acp script for automated Git operations (21df196)
- feat ✨: Add main entry point for git-acp package (a67d6e7)
- feat ✨: Add Git Add-Commit-Push Automation Package (28e2264)
- feat ✨: Add setup.py for git-acp (3719ddc)
- feat ✨: Add requirements file for Python dependencies (ec21559)

## [0.5.0] - 10-01-2025

### Initial Setup
- feat ✨: Initial commit (f7edbdd)
- feat ✨: Make git-acp.sh executable (7b3e282)
- feat ✨: Add new Bash script for automating Git actions with Ollama (9532c36)

---
