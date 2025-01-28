# Introduction

The `git-acp` package is a powerful command-line tool designed to streamline Git operations by automating the add, commit, and push workflow with intelligent features. It combines traditional Git functionality with modern AI capabilities to enhance your development workflow.

## Key Features

- **Smart Interactive Mode**
  - Interactive file selection with status indicators
  - Intelligent commit type suggestions based on changes
  - Beautiful CLI interface with color-coded output

- **AI-Powered Commit Messages**
  - Integration with Ollama AI for generating descriptive commit messages
  - Context-aware message generation using repository history
  - Support for both simple and advanced message generation modes

- **Conventional Commits Support**
  - Automatic commit type classification
  - Emoji support for commit messages
  - Standardized commit message format

- **Enhanced Git Operations**
  - Automated add, commit, and push in a single command
  - Smart branch detection and management
  - Comprehensive error handling with descriptive messages

- **Rich Configuration Options**
  - Environment variable customization
  - Command-line arguments for fine-grained control
  - Configurable AI settings and commit message formats

## Architecture

The package is organized into several key components:

- **CLI Module**: Handles command-line interface and user interaction
- **Git Module**: Manages core Git operations and repository interactions
- **AI Module**: Provides AI-powered commit message generation
- **Config Module**: Manages configuration and environment settings
- **Utils Module**: Contains utility functions and helper classes

## Design Philosophy

`git-acp` is built with the following principles in mind:

1. **Simplicity**: Streamline common Git workflows into single commands
2. **Intelligence**: Use AI and pattern recognition to enhance Git operations
3. **Safety**: Provide clear feedback and confirmation steps for critical operations
4. **Extensibility**: Modular design for easy feature additions and customizations
5. **User Experience**: Rich terminal output with progress indicators and color coding

## Prerequisites

- Python 3.6 or higher
- Git installed and configured
- Ollama installed (optional, for AI features)
- pipx (recommended for installation)
