# Quick Start

## Installation

### Recommended: Global Installation with pipx

`pipx` is the recommended way to install Python CLI applications globally. It creates isolated environments for each application, ensuring dependency conflicts are avoided.

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
    pipx install "git+https://github.com/beecave-homelab/git-acp.git"
    ```

### Alternative: Install with pip

To install the `git_acp` package using pip:

```bash
pip install git_acp
```

## Setup

After installation, you can start using the package by importing it in your Python scripts:

```python
import git_acp
```

## Basic Usage

Here's a simple example of how to use `git_acp` to add and commit changes:

```python
from git_acp.git.git_operations import git_add, git_commit

# Add files to staging
files_to_add = 'README.md'
git_add(files_to_add)

# Commit changes
commit_message = 'Update README with installation instructions'
git_commit(commit_message)
```

## Key Features

- **Interactive Mode**: Automatically stages files, suggests commit types, and generates commit messages.
- **AI-Powered Commit Messages**: Use Ollama AI to generate descriptive commit messages.
- **Command-Line Options**: Customize operations with options like `-a` for adding files, `-mb` for commit message bodies, and `-b` for specifying branches.
- **Verbose Output**: Use `-v` for detailed debug information.

This guide provides a basic overview to get you started. For more detailed usage, refer to the advanced usage section.
