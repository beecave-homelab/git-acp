# git-acp

A Python tool to automate Git add, commit, and push actions with optional AI-generated commit messages using Ollama. Features a beautiful CLI interface with color-coded output and progress indicators.

## Versions

**Current version**: 0.9.1

## Table of Contents

- [Versions](#versions)
- [Badges](#badges)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)
- [Contributing](#contributing)

## Badges

![Python](https://img.shields.io/badge/python-3.6%2B-blue)
![Version](https://img.shields.io/badge/version-0.9.1-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- Automates git add, commit, and push operations
- Supports AI-generated commit messages using Ollama
- Interactive commit type selection with automatic suggestions
- Beautiful CLI interface with color-coded output
- Progress indicators for long-running operations
- Follows conventional commit message format
- Configurable through command-line arguments
- Interactive confirmation prompts (optional)

## Prerequisites

- Python 3.6 or higher
- Git installed and configured
- Ollama installed (optional, for AI-generated commit messages)
- pipx (optional, for global installation)

## Installation

### Option 1: Global Installation with pipx (Recommended)

[pipx](https://pypa.github.io/pipx/) is the recommended way to install Python CLI applications globally. It creates isolated environments for each application, ensuring dependency conflicts are avoided.

1. Install pipx if you haven't already:

    ```bash
    # On macOS
    brew install pipx
    pipx ensurepath

    # On Linux
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    ```

2. Install git-acp:

    ```bash
    # Install from GitHub
    pipx install "git+https://github.com/beecave-homelab/git-acp.git"

    # Or install from local directory (if you've cloned the repo)
    pipx install .
    ```

The command `git-acp` will now be available globally in your system.

To upgrade to the latest version:

```bash
pipx upgrade git-acp
```

To uninstall:

```bash
pipx uninstall git-acp
```

### Option 2: Install in a Virtual Environment

1. Clone the repository:

    ```bash
    git clone https://github.com/beecave-homelab/git-acp.git
    cd git-acp
    ```

2. Create and activate a virtual environment:

    ```bash
    # Create virtual environment
    python -m venv venv

    # Activate on macOS/Linux
    source venv/bin/activate

    # Activate on Windows
    # .\venv\Scripts\activate
    ```

3. Install the package:

    ```bash
    pip install .
    ```

### Option 3: Install Directly with pip

Not recommended for CLI tools, but possible:

```bash
pip install git+https://github.com/beecave-homelab/git-acp.git
```

## Usage

After installation, you can use the `git-acp` command from anywhere in your terminal:

```bash
git-acp [OPTIONS]
```

### Options

- `-a, --add <file>`: Add specified file(s). If not specified, shows interactive file selection.
- `-m, --message <msg>`: Commit message. Defaults to 'Automated commit'.
- `-b, --branch <branch>`: Specify the branch to push to. Defaults to the current active branch.
- `-o, --ollama`: Use Ollama AI to generate the commit message.
- `-nc, --no-confirm`: Skip confirmation prompts for all actions.
- `-t, --type <type>`: Override automatic commit type suggestion.
- `-v, --verbose`: Show debug information.
- `-h, --help`: Show help message.

### Examples

1. Basic usage with interactive file and commit type selection:

    ```bash
    git-acp
    ```

2. Specify files to add and commit message:

    ```bash
    git-acp -a "file1.py file2.py" -m "Add new features"
    ```

3. Use AI-generated commit message:

    ```bash
    git-acp -o
    ```

4. Push to a specific branch:

    ```bash
    git-acp -b main -m "Update documentation"
    ```

5. Skip confirmation prompts:

    ```bash
    git-acp -nc -m "Quick fix"
    ```

6. Override commit type suggestion:

    ```bash
    git-acp -t docs
    ```

## Commit Types

The tool suggests commit types based on the changes and allows interactive selection:

- ✨ feat: New features
- 🐛 fix: Bug fixes
- 📝 docs: Documentation changes
- 💎 style: Code style changes
- ♻️ refactor: Code refactoring
- 🧪 test: Adding or modifying tests
- 📦 chore: Maintenance tasks
- ⏪ revert: Reverting changes

The suggested type appears first in the selection list, but you can choose any type using the arrow keys.

## License

This project is licensed under the MIT license. See [LICENSE](LICENSE) for more information.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
