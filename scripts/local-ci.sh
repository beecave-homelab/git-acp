#!/bin/bash
set -euo pipefail

# Script Description: Run local CI pipeline (fix, format, test, coverage)
# Author: elvee
# Version: 0.2.0
# License: MIT
# Creation Date: 03/12/2025
# Last Modified: 15/01/2026
# Usage: local-ci.sh

# Constants
DEFAULT_OUTPUT_FILE="${PWD}/ci-output.log"

# ASCII Art (Calvin font)
print_ascii_art() {
  echo "
╦    ╔═╗  ╔═╗  ╔═╗  ╦         ╔═╗  ╦
║    ║ ║  ║    ╠═╣  ║    ───  ║    ║
╩═╝  ╚═╝  ╚═╝  ╩ ╩  ╩═╝       ╚═╝  ╩
"
}

# Help
show_help() {
  echo "
Usage: $0 [OPTIONS]

Options:
  -o, --output_file FILE     Write CI logs to file (default: $DEFAULT_OUTPUT_FILE)
  -i, --install-deps         Install missing dependencies on Linux (pdm via pip, tee via coreutils)
  -h, --help                 Show help

This script performs:
  • pdm run fix
  • pdm run format
  • pdm run test
  • pdm run test-cov
  • pdm run docstring-coverage
  • pdm run mypy -p git_acp -p tests
"
}

# Error handling
error_exit() {
  echo "Error: $1" >&2
  exit 1
}

is_linux() {
  [[ "$(uname -s)" == "Linux" ]]
}

resolve_pip_command() {
  if command -v pip >/dev/null 2>&1; then
    echo "pip"
    return 0
  fi

  if command -v pip3 >/dev/null 2>&1; then
    echo "pip3"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    echo "python3 -m pip"
    return 0
  fi

  return 1
}

install_pdm() {
  local pip_command
  if ! pip_command="$(resolve_pip_command)"; then
    error_exit "pip not found. Install pip, then run: pip install pdm"
  fi

  echo "[+] Installing pdm..."
  ${pip_command} install --user pdm

  local user_base
  user_base="$(${pip_command% -m pip} -m site --user-base 2>/dev/null)"
  if [[ -z "${user_base}" ]]; then
    user_base="${HOME}/.local"
  fi
  if [[ ":${PATH}:" != *":${user_base}/bin:"* ]]; then
    export PATH="${user_base}/bin:${PATH}"
  fi
  hash -r
}

install_coreutils() {
  local sudo_command=""
  if command -v sudo >/dev/null 2>&1; then
    sudo_command="sudo"
  fi

  if command -v apt-get >/dev/null 2>&1; then
    echo "[+] Installing coreutils via apt-get..."
    ${sudo_command} apt-get update
    ${sudo_command} apt-get install -y coreutils
    return 0
  fi

  if command -v dnf >/dev/null 2>&1; then
    echo "[+] Installing coreutils via dnf..."
    ${sudo_command} dnf install -y coreutils
    return 0
  fi

  if command -v yum >/dev/null 2>&1; then
    echo "[+] Installing coreutils via yum..."
    ${sudo_command} yum install -y coreutils
    return 0
  fi

  if command -v pacman >/dev/null 2>&1; then
    echo "[+] Installing coreutils via pacman..."
    ${sudo_command} pacman -Sy --noconfirm coreutils
    return 0
  fi

  if command -v apk >/dev/null 2>&1; then
    echo "[+] Installing coreutils via apk..."
    ${sudo_command} apk add --no-cache coreutils
    return 0
  fi

  if command -v zypper >/dev/null 2>&1; then
    echo "[+] Installing coreutils via zypper..."
    ${sudo_command} zypper install -y coreutils
    return 0
  fi

  error_exit "No supported package manager found to install coreutils. Install it manually."
}

install_missing_dependencies() {
  if ! is_linux; then
    error_exit "Auto-install is supported only on Linux. Install dependencies manually."
  fi

  for dependency in "$@"; do
    case "${dependency}" in
      pdm)
        install_pdm
        ;;
      tee)
        install_coreutils
        ;;
      *)
        error_exit "Unknown dependency: ${dependency}"
        ;;
    esac
  done
}

ensure_dependencies() {
  local install_deps="$1"
  local missing=()

  if ! command -v pdm >/dev/null 2>&1; then
    missing+=("pdm")
  fi

  if ! command -v tee >/dev/null 2>&1; then
    missing+=("tee")
  fi

  if [[ ${#missing[@]} -eq 0 ]]; then
    return 0
  fi

  if [[ "${install_deps}" == "true" ]]; then
    install_missing_dependencies "${missing[@]}"
  else
    error_exit "Missing dependencies: ${missing[*]}. Install them or rerun with --install-deps."
  fi

  for dependency in "${missing[@]}"; do
    if ! command -v "${dependency}" >/dev/null 2>&1; then
      error_exit "Dependency installation failed: ${dependency}. Please install it manually."
    fi
  done
}

# Main logic
main_logic() {
  echo "[+] The following tasks will be executed:"
  echo "    • pdm run fix"
  echo "    • pdm run format"
  echo "    • pdm run test"
  echo "    • pdm run test-cov"
  echo "    • pdm run docstring-coverage"
  echo "    • pdm run mypy -p git_acp -p tests"
  echo ""

  local output_file="$1"

  {
    echo "[+] Running fix..."
    echo ""
    pdm run fix
    echo ""
    echo "[+] Running format..."
    pdm run format
    echo ""
    echo "[+] Running tests..."
    pdm run test
    echo ""
    echo "[+] Running test coverage..."
    pdm run test-cov
    echo ""
    echo "[+] Running docstring coverage..."
    pdm run docstring-coverage
    echo ""
    echo "[+] Running mypy..."
    pdm run mypy -p git_acp -p tests
    echo ""
    echo "[+] Local CI check successful. You can commit these changes."
  } | tee "${output_file}"
}

# Main
main() {
  local output_file="$DEFAULT_OUTPUT_FILE"
  local install_deps="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output_file)
        output_file="$2"
        shift 2
        ;;
      -i|--install-deps)
        install_deps="true"
        shift
        ;;
      -h|--help)
        show_help
        exit 0
        ;;
      *)
        error_exit "Invalid option: $1"
        ;;
    esac
  done

  ensure_dependencies "$install_deps"
  main_logic "$output_file"
}

# Header ASCII art
print_ascii_art

# Execute
main "$@"
