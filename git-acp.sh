#!/bin/bash

# Script Description: This script automates Git add, commit, and push actions with optional AI-generated commit messages using Ollama.
# Author: elvee
# Version: 0.5.0
# License: MIT
# Creation Date: 20/12/2024
# Last Modified: 20/12/2024

# Constants
set -euo pipefail

# Commit type mappings as full strings
FEAT="feat ✨"
FIX="fix 🐛"
DOCS="docs 📝"
STYLE="style 💎"
REFACTOR="refactor ♻️"
TEST="test 🧪"
CHORE="chore 📦"
REVERT="revert ⏪"

# Function to display help
show_help() {
  echo "Usage: $(basename "$0") [OPTIONS]"
  echo "Options:"
  echo "  -a, --add <file>       Add specified file(s). Defaults to all changed files."
  echo "  -m, --message <msg>    Commit message. Defaults to 'Automated commit'."
  echo "  -b, --branch <branch>  Specify the branch to push to. Defaults to the current active branch."
  echo "  -o, --ollama           Use Ollama AI to generate the commit message."
  echo "  -nc, --no-confirm      Skip confirmation prompts for all actions, including the Ollama-generated commit message."
  echo "  -h, --help             Show this help message."
}

# Function to add files
git_add() {
  local files="${1:-.}"
  if ! git add "$files"; then
    echo "Error: Failed to add files."
    exit 1
  fi
}

# Function to commit changes
git_commit() {
  local message="$1"
  if ! git commit -m "${message}"; then
    echo "Error: Failed to commit changes."
    exit 1
  fi
}

# Function to push changes
git_push() {
  local branch="$1"
  if ! git push origin "${branch}"; then
    echo "Error: Failed to push changes to branch '$branch'."
    exit 1
  fi
}

# Function to get current branch
get_current_branch() {
  local branch
  if ! branch=$(git rev-parse --abbrev-ref HEAD); then
    echo "Error: Failed to get the current branch."
    exit 1
  fi
  echo "$branch"
}

# Function to generate a commit message using Ollama
generate_commit_message_with_ollama() {
  local commit_message
  if ! commit_message=$(git diff | ollama run mevatron/diffsense:1.5b); then
    echo "Error: Failed to generate commit message with Ollama."
    exit 1
  fi
  echo "$commit_message"
}

# Function to classify the commit type based on git diff
classify_commit_type() {
  local diff
  diff=$(git diff)

  # Prioritize "feat" detection
  if [[ "$diff" == *"add"* || "$diff" == *"new"* || "$diff" == *"feature"* || \
        "$diff" == *"update"* || "$diff" == *"introduce"* || "$diff" == *"implement"* || \
        "$diff" == *"enhance"* || "$diff" == *"create"* || "$diff" == *"improve"* || \
        "$diff" == *"support"* ]]; then
    echo "$FEAT"

  # Check for "fix" keywords
  elif [[ "$diff" == *"fix"* || "$diff" == *"bug"* || "$diff" == *"patch"* || "$diff" == *"issue"* ]]; then
    echo "$FIX"

  # Check for "docs" related changes
  elif [[ "$diff" == *"docs/"* || "$diff" == *".md"* || "$diff" == *"README"* ]]; then
    echo "$DOCS"

  # Check for "refactor" keywords
  elif [[ "$diff" == *"refactor"* || "$diff" == *"restructure"* || "$diff" == *"cleanup"* ]]; then
    echo "$REFACTOR"

  # Check for "test" changes
  elif [[ "$diff" == *"test"* || "$diff" == *".test."* || "$diff" == *"spec"* ]]; then
    echo "$TEST"

  # Check for "style" changes
  elif [[ "$diff" == *"style"* || "$diff" == *"format"* || "$diff" == *"whitespace"* || "$diff" == *"lint"* ]]; then
    echo "$STYLE"

  # Check for "revert" changes
  elif [[ "$diff" == *"revert"* ]]; then
    echo "$REVERT"

  # Default to "chore"
  else
    echo "$CHORE"
  fi
}

# Function to format the commit message according to user preferences
format_commit_message() {
  local commit_type="${1:-$CHORE}"
  local message="${2:-Automated commit}"

  local title
  title=$(echo "$message" | head -n 1)
  local description
  description=$(echo "$message" | tail -n +2)

  local formatted_message="${commit_type}: ${title}\n\n${description}"
  echo -e "$formatted_message"
}

# Main function
main() {
  local add_files=""
  local commit_message=""
  local branch=""
  local use_ollama=false
  local skip_confirmation=false

  while [[ "$#" -gt 0 ]]; do
    case $1 in
      -a|--add)
        add_files="$2"
        shift 2
        ;;
      -m|--message)
        commit_message="$2"
        shift 2
        ;;
      -b|--branch)
        branch="$2"
        shift 2
        ;;
      -o|--ollama)
        use_ollama=true
        shift 1
        ;;
      -nc|--no-confirm)
        skip_confirmation=true
        shift 1
        ;;
      -h|--help)
        show_help
        exit 0
        ;;
      *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
    esac
  done

  branch="${branch:-$(get_current_branch)}"

  if [[ "$use_ollama" == true ]]; then
    commit_message=$(generate_commit_message_with_ollama)
  fi

  if [[ -z "$commit_message" ]]; then
    echo "Error: No commit message provided."
    exit 1
  fi

  local commit_type
  commit_type=$(classify_commit_type)
  commit_message=$(format_commit_message "$commit_type" "$commit_message")

  if [[ "$skip_confirmation" != true ]]; then
    echo "Commit message: $commit_message"
    read -p "Do you want to proceed? (y/n): " confirmation
    if [[ "$confirmation" != "y" ]]; then
      echo "Operation cancelled."
      exit 0
    fi
  fi

  git_add "$add_files"
  git_commit "$commit_message"
  git_push "$branch"
}

main "$@"