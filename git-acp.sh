#!/bin/bash

# Script Description: This script automates Git add, commit, and push actions with optional AI-generated commit messages using Ollama.
# Author: elvee
# Version: 0.4.0
# License: MIT
# Creation Date: 20-12-2024
# Last Modified: 20-12-2024

# Constants
set -euo pipefail

# Function to display help
show_help() {
  echo "Usage: $(basename "$0") [OPTIONS]"
  echo "Options:"
  echo "  -a, --add <file>       Add specified file(s). Defaults to all changed files."
  echo "  -m, --message <msg>    Commit message. Defaults to 'Automated commit'."
  echo "  -b, --branch <branch>  Specify the branch to push to. Defaults to the current active branch."
  echo "  -o, --ollama           Use Ollama AI to generate the commit message. This requires Ollama to be installed"
  echo "                         and the 'mevatron/diffsense:1.5b' model to be available locally."
  echo "  -nc, --no-confirm      Skip confirmation prompts for all actions, including the Ollama-generated commit message."
  echo "  -h, --help             Show this help message."
  echo
  echo "Example:"
  echo "  $(basename "$0") -a \"file1 file2\" -m \"Initial commit\" -b \"develop\""
  echo "  This will add 'file1' and 'file2' to the staging area, commit with the message 'Initial commit',"
  echo "  and push the changes to the 'develop' branch."
  echo
  echo "  $(basename "$0") -a \"file1 file2\" -o"
  echo "  This will add 'file1' and 'file2' to the staging area, generate the commit message using"
  echo "  Ollama (via the command 'git diff | ollama run mevatron/diffsense:1.5b'), and push the changes to the current branch."
  echo
  echo "  $(basename "$0") -a \"file1 file2\" -o -nc"
  echo "  This will add 'file1' and 'file2', generate the commit message using Ollama, and commit and push without asking for confirmation."
}

# Function to add files
git_add() {
  local files="$1"
  if ! git add ${files:-.}; then
    echo "Error: Failed to add files."
    exit 1
  fi
}

# Function to commit changes
git_commit() {
  local message="$1"
  if ! git commit -m "${message:-Automated commit}"; then
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

# Function to confirm before pushing
confirm_and_push() {
  local files="$1"
  local message="$2"
  local branch="$3"
  local skip_confirmation="$4"

  if [[ "$skip_confirmation" != true ]]; then
    echo "Files to be added: ${files:-All changed files}"
    echo "Commit message: ${message:-Automated commit}"
    echo "Branch to push to: $branch"
    read -p "Do you want to proceed? (y/n): " confirmation
    if [[ "$confirmation" != "y" ]]; then
      echo "Operation cancelled."
      exit 0
    fi
  fi

  # Add files
  git_add "$files"
  # Commit changes
  git_commit "$message"
  # Push changes
  git_push "$branch"
}

# Main function
main() {
  local add_files=""
  local commit_message=""
  local branch=""
  local use_ollama=false
  local skip_confirmation=false

  # Parse command-line arguments
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

  # Get the current branch if not specified
  branch=${branch:-$(get_current_branch)}

  # Generate commit message using Ollama if the option is enabled
  if [[ "$use_ollama" == true ]]; then
    commit_message=$(generate_commit_message_with_ollama)
    echo "Generated commit message using Ollama: $commit_message"

    if [[ "$skip_confirmation" != true ]]; then
      read -p "Do you want to use this commit message? (y/n): " confirmation
      if [[ "$confirmation" != "y" ]]; then
        echo "Operation cancelled."
        exit 0
      fi
    fi
  fi

  # Confirm before pushing
  confirm_and_push "$add_files" "$commit_message" "$branch" "$skip_confirmation"
}

# Execute main function
main "$@"