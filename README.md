# git-acp

A Python tool to automate Git add, commit, and push actions with optional AI-generated commit messages using Ollama. Features a beautiful CLI interface with color-coded output and progress indicators.

![GIT-ACP logo](./assets/logo/git-acp-logo-textonly.png)

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Version](https://img.shields.io/badge/version-0.17.0-brightgreen)
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
- AI-powered commit messages via Ollama
- Interactive file selection and type suggestions
- Conventional commits with emoji support
- Color-coded terminal interface
- Configurable through CLI options and environment variables

## Installation

### Recommended: Global Installation with pipx

```bash
pipx install "git+https://github.com/beecave-homelab/git-acp.git"
```

For other installation methods and detailed instructions, see the [Installation Guide](docs/getting_started/installation.md).

## Quick Start

```bash
# Interactive mode
git-acp

# Commit specific files with message
git-acp -a "README.md src/*.py" -m "Update documentation"

# AI-generated commit message
git-acp -o
```

![git-acp interactive mode](./assets/examples/git-acp-example-output-default.gif)

For more usage examples and advanced features, refer to:

- [Basic Usage Guide](docs/usage/basic_usage.md)
- [Advanced Usage Guide](docs/usage/advanced_usage.md)

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

See [Advanced Usage](docs/usage/advanced_usage.md#advanced-usage) for all available options.

## Documentation

- [API Reference](docs/api/overview.md)
- [Getting Started](docs/getting_started/introduction.md)
- [Usage](docs/usage/basic_usage.md)
- [Testing Overview](docs/tests/test_plan.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
