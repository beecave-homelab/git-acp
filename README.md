# git-acp

A Python tool to automate Git add, commit, and push actions with optional AI-generated commit messages using Ollama. Features a beautiful CLI interface with color-coded output and progress indicators.

![GIT-ACP logo](./assets/logo/git-acp-logo-textonly.png)

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Version](https://img.shields.io/badge/version-0.19.0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [License](#license)

## Features

- Single-command Git workflow automation
- AI-powered commit messages via Ollama with two prompt modes:
  - **Simple**: Fast generation with basic context
  - **Advanced**: Rich repository context for style-aware messages (default)
- Interactive file selection and type suggestions
- Conventional commits with emoji support
- Consistent "all files" selection: choose **All files** in the prompt or use `-a .` to stage everything while still listing each file before commit.
- Color-coded terminal interface
- Configurable through CLI options and environment variables

## Installation

### Recommended: Global Installation with pipx

```bash
pipx install "git+https://github.com/beecave-homelab/git-acp.git"
```

For other installation methods and detailed instructions, see [`installation.md`](docs/getting_started/installation.md).

## Quick Start

```bash
# Interactive mode
git-acp

# Commit specific files with message
git-acp -a "README.md src/*.py" -mb "Update documentation"

# AI-generated commit message
git-acp -o
```

![git-acp interactive mode](./assets/examples/git-acp-example-output-default.gif)

For more usage examples and advanced features, refer to:

- [`basic_usage.md`](docs/usage/basic_usage.md)
- [`advanced_usage.md`](docs/usage/advanced_usage.md)

## Configuration

Configure settings by copying the provided example file and adjusting values:

```bash
mkdir -p ~/.config/git-acp
cp .env.example ~/.config/git-acp/.env
nano ~/.config/git-acp/.env  # Adjust values as needed
```

Example configuration (`~/.config/git-acp/.env`):

```ini
# Example configuration
GIT_ACP_AI_MODEL=mevatron/diffsense:1.5b
GIT_ACP_DEFAULT_BRANCH=main
```

See [`advanced_usage.md`](docs/usage/advanced_usage.md#advanced-usage) for all available options.

## Documentation

- [`overview.md`](docs/api/overview.md)
- [`introduction.md`](docs/getting_started/introduction.md)
- [`basic_usage.md`](docs/usage/basic_usage.md)
- [`test_plan.md`](docs/tests/test_plan.md)

## License

This project is licensed under the MIT License - see the [`LICENSE`](LICENSE) file for details.
