# Installation

This guide provides detailed instructions for installing `git-acp` and its dependencies.

## Prerequisites

### Required Software

- Python 3.6 or higher
- Git
- pip or pipx

### Optional Dependencies

- Ollama (for AI features)

## Installation Methods

### 1. Global Installation with pipx (Recommended)

[pipx](https://pypa.github.io/pipx/) is the recommended way to install Python CLI applications globally. It creates isolated environments for each application, ensuring dependency conflicts are avoided.

#### Install pipx

On macOS:

```bash
brew install pipx
pipx ensurepath
```

On Linux:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

On Windows:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

#### Install git-acp

```bash
pipx install "git+https://github.com/beecave-homelab/git-acp.git"
```

#### Upgrade git-acp

```bash
pipx upgrade git-acp
```

#### Uninstall git-acp

```bash
pipx uninstall git-acp
```

### 2. Install in a Virtual Environment

#### Create Virtual Environment

```bash
# Clone repository
git clone https://github.com/beecave-homelab/git-acp.git
cd git-acp

# Create virtual environment
python -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows
# .\venv\Scripts\activate
```

#### Install Package

```bash
pip install .
```

### 3. Direct Installation with pip

Not recommended for CLI tools, but possible:

```bash
pip install git+https://github.com/beecave-homelab/git-acp.git
```

## Ollama Setup (Optional)

For AI-powered commit message generation:

### 1. Install Ollama

On macOS/Linux:

```bash
curl https://ollama.ai/install.sh | sh
```

For other platforms, visit [Ollama's website](https://ollama.ai).

### 2. Start Ollama Server

```bash
ollama serve
```

### 3. Pull Recommended Model

```bash
ollama pull mevatron/diffsense:1.5b
```

## Verification

### Check Installation

```bash
git-acp --version
```

### Test Basic Functionality

```bash
git-acp --help
```

### Verify AI Features

```bash
# Test Ollama connection
git-acp -o --test-ai
```

## Configuration

### Create Configuration Directory

```bash
mkdir -p ~/.config/git-acp
```

### Set Up Environment

Create `~/.config/git-acp/.env`:

```ini
# Basic Configuration
GIT_ACP_DEFAULT_BRANCH=main
GIT_ACP_DEFAULT_REMOTE=origin

# AI Configuration (if using Ollama)
GIT_ACP_AI_MODEL=mevatron/diffsense:1.5b
GIT_ACP_BASE_URL=http://localhost:11434/v1
```

## Troubleshooting

### Common Issues

#### Package Not Found

```bash
# Ensure Python and pip are up to date
python -m pip install --upgrade pip
```

#### Permission Issues

```bash
# Install with user permissions
pip install --user git+https://github.com/beecave-homelab/git-acp.git
```

#### Path Issues

```bash
# Add to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"
```

### System-Specific Notes

#### macOS

- Use Homebrew for dependencies
- Consider using pipx

#### Linux

- Install system dependencies
- Use distribution package manager
- Check file permissions
