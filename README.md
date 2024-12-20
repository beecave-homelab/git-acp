# git-acp

A Python tool to automate Git add, commit, and push actions with optional AI-generated commit messages using Ollama. Features a beautiful CLI interface with color-coded output and progress indicators.

## Features

- Automates git add, commit, and push operations
- Supports AI-generated commit messages using Ollama
- Automatically classifies commit types with appropriate emojis
- Beautiful CLI interface with color-coded output
- Progress indicators for long-running operations
- Follows conventional commit message format
- Configurable through command-line arguments
- Interactive confirmation prompts (optional)

## Prerequisites

- Python 3.6 or higher
- Git installed and configured
- Ollama installed (optional, for AI-generated commit messages)

## Installation

### Option 1: Install in a Virtual Environment (Recommended)

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

### Option 2: Install Directly from GitHub

```bash
pip install git+https://github.com/beecave-homelab/git-acp.git
```

## Usage

After installation, you can use the `git-acp` command from anywhere in your terminal:

```bash
git-acp [OPTIONS]
```

### Options

- `-a, --add <file>`: Add specified file(s). Defaults to all changed files.
- `-m, --message <msg>`: Commit message. Defaults to 'Automated commit'.
- `-b, --branch <branch>`: Specify the branch to push to. Defaults to the current active branch.
- `-o, --ollama`: Use Ollama AI to generate the commit message.
- `-nc, --no-confirm`: Skip confirmation prompts for all actions.
- `-h, --help`: Show help message.

### Examples

1. Basic usage (adds all files, uses default commit message):
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

## Commit Types

The tool automatically classifies commits into the following types:

- ✨ feat: New features
- 🐛 fix: Bug fixes
- 📝 docs: Documentation changes
- 💎 style: Code style changes
- ♻️ refactor: Code refactoring
- 🧪 test: Adding or modifying tests
- 📦 chore: Maintenance tasks
- ⏪ revert: Reverting changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

elvee

## Version

0.5.0
