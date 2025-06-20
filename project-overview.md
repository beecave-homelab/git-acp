---
repo: https://github.com/beecave-homelab/git-acp.git
commit: 3f7b6d4249527965c5cc4e7346b02cf6455118e0
generated: 2025-06-20T00:00:00Z
---
<!-- SECTIONS:CLI,API -->

# Project Overview | git-acp

`git-acp` is a command-line tool that automates the `git add`, `commit`, and `push` workflow. It offers interactive file selection, AI-powered commit message generation via Ollama, and enforces Conventional Commits standards.

[![Language](https://img.shields.io/badge/Python-3.10+-blue)]
[![Version](https://img.shields.io/badge/Version-0.15.0-brightgreen)](#version-summary)
[![CLI](https://img.shields.io/badge/CLI-Click-blue)](#cli)

## Table of Contents

- [Quickstart for Developers](#quickstart-for-developers)
- [Version Summary](#version-summary)
- [Project Features](#project-features)
- [Project Structure](#project-structure)
- [Architecture Highlights](#architecture-highlights)
- [CLI](#cli)
- [API](#api)

## Quickstart for Developers

```bash
# Recommended installation with pipx
pipx install "git+https://github.com/beecave-homelab/git-acp.git"

# Local development setup
git clone https://github.com/beecave-homelab/git-acp.git
cd git-acp
pip install pdm # if not already installed
pdm install -G dev && pdm run git-acp --help
```

## Version Summary

| Version | Date       | Type | Key Changes                |
|---------|------------|------|----------------------------|
| 0.15.0  | 2025-06-20 | ✨   | Enhanced CLI & version bump |
| 0.14.1  | YYYY-MM-DD | ✨   | Initial project setup      |

## Project Features

- Interactive staging of changed files.
- AI-generated commit messages using Ollama.
- Automatic classification of commit types (feat, fix, etc.).
- Support for Conventional Commits specification.
- Rich terminal output for better user experience.
- Skipping confirmation prompts for faster workflow.
- Verbose mode for debugging.

## Project Structure

<details><summary>Show tree</summary>

```text
git_acp/
├── __init__.py             # Exposes the package version.
├── __main__.py             # Main entry point, calls the CLI.
├── ai/
│   ├── __init__.py         # Exposes the commit message generation function.
│   └── ai_utils.py         # Handles interaction with the Ollama AI.
├── cli/
│   ├── __init__.py         # Exposes the main CLI function.
│   └── cli.py              # Defines the command-line interface using Click.
├── commit/                 # (empty) Intended for future commit-related logic.
├── pr/                     # (empty) Intended for future pull request helpers.
├── config/
│   ├── __init__.py         # Exposes all configuration constants and functions.
│   ├── constants.py        # Defines static configuration values and defaults.
│   └── env_config.py       # Manages loading of environment variables.
├── git/
│   ├── __init__.py         # Exposes all public Git operation functions.
│   ├── classification.py   # Classifies commit types based on file changes.
│   └── git_operations.py   # Wraps core Git commands (add, commit, push, etc.).
└── utils/
    ├── __init__.py         # Exposes utility functions and types.
    ├── formatting.py       # Provides styled terminal output functions.
    └── types.py            # Defines custom data types and type aliases.
```

</details>

## Architecture Highlights

- The application is built around the `click` library for its CLI.
- It uses `questionary` for interactive prompts, providing a user-friendly way to select files and commit types.
- `rich` is used for formatted and colored terminal output.
- The core logic is modular, with separate packages for AI, CLI, git operations, and configuration.
- A `GitConfig` class is used to manage configuration state throughout the application.

## CLI

The main entry point is `git_acp.cli.cli.main`. It provides a set of options to control the git workflow.

**Options:**

- `-a, --add`: Specify files to stage.
- `-m, --message`: Provide a custom commit message.
- `-b, --branch`: Target branch for push.
- `-t, --type`: Manually specify commit type.
- `-o, --ollama`: Use AI to generate commit message.
- `-i, --interactive`: Interactively edit AI-generated message.
- `-nc, --no-confirm`: Skip confirmation prompts.
- `-v, --verbose`: Enable verbose output.
- `-p, --prompt-type`: Select AI prompt complexity.

## API
>
> This project does not expose a public API. It is intended to be used as a command-line tool.

**Always update this file when code or configuration changes.**
