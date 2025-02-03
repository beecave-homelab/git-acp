# Release Notes - Version 0.15.0 (01-02-2025)

This release introduces significant architectural improvements and refactoring across multiple components of git-acp. The changes focus on enhancing modularity, improving code organization, and establishing better separation of concerns throughout the codebase.

## Module Improvements

### Git Operations ♻️

- Split monolithic `git_operations.py` into specialized modules:
  - `runner.py`: Core Git command execution and error handling
  - `history.py`: Commit history and diff analysis
  - `remote.py`: Remote repository management
  - `stash.py`: Stash operations
  - `status.py`: File status tracking
  - `tag.py`: Tag management

### AI System 🤖

- Reorganized AI functionality into focused components:
  - `client.py`: Improved AI client with better request handling
  - `generation.py`: Streamlined commit message generation
  - `commit_prompts.py`: Centralized system prompts management

### Command Line Interface 🖥️

- Enhanced CLI structure with better separation of concerns:
  - `cli.py`: Streamlined command orchestration
  - `prompts.py`: User interaction management
  - `helpers.py`: CLI utility functions
  - `formatting.py`: Terminal output formatting

### Configuration System ⚙️

- Improved configuration management with:
  - `settings.py`: Centralized settings management
  - `loader.py`: Environment configuration loading
  - `constants.py`: Project-wide constants
  - `env_config.py`: Environment variable handling

### Utility Functions 🛠️

- Reorganized utility functions for better reusability:
  - `formatting.py`: Rich terminal output utilities
  - `types.py`: Type definitions and contracts
  - Clear exports through `__init__.py` files

## Commit History

### Refactoring ♻️

- Add main CLI entry point and update `__init__.py` for improved package structure (6b7ed52)
- Add Git history and diff analysis, remote management, stash operations, and status tracking capabilities (4bd8052)
- Add configuration loader and settings modules for centralized configuration management (c10535e)
- Refactor CLI imports and add new formatting and helper functions for better user experience (456e9be)
- Refactor AI commit message generation to use new client and prompts for improved message quality (f25958f)

### Package Management 📦

- Bump version to 0.15.0 in `README.md`, `init.py`, and `setup.py` (a52f1f8)

## Key Benefits

- **Enhanced Modularity**: Each component now has a clear, single responsibility
- **Better Maintainability**: Improved code organization and documentation
- **Easier Testing**: Modular design enables more focused and comprehensive testing
- **Improved Developer Experience**: Better code navigation and understanding
- **Future-Ready**: Strong foundation for future features and improvements

## Upgrade Instructions

No breaking changes were introduced in this version. Users can upgrade directly from previous versions without any additional steps required.

For more detailed information about the changes, please refer to the [CHANGELOG.md](CHANGELOG.md).
