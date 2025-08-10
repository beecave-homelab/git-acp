# Versions

## **v0.17.0** (Current) - *10-08-2025*

#### ✨/🔄 Brief Description

Minor feature release with refactors. Introduces a configurable fallback Ollama server and flattens the Git operations structure for maintainability. Includes test additions.

#### ✨ **New Features in v0.17.0**

- Added: Configurable fallback Ollama server

#### 🔧 **Improvements in v0.17.0**

- Refactor: Flattened Git operations package structure
- Refactor: Internal cleanups across Git helpers
- Tests: Added basic to-do test scaffold

#### 📝 **Key Commits in v0.17.0**

`f14f674`, `35960dd`, `3102ffb`, `57a2633`

---

## **v0.16.0** - *August 2025*

#### ✨/🔄 Brief Description

Refactors across AI and Git helpers, dependency updates, and general enhancements.

#### ✨ **New Features in v0.16.0** (if any)

- Enhanced project structure and CLI improvements.

#### 🐛 **Bug Fixes in v0.16.0** (if any)

- Fixed: Improve CLI add-path handling and enhance tests.
  - Issue: Incorrect handling of the -a flag paths in certain cases.
  - Root Cause: Argument parsing and path normalization edge cases.
  - Solution: Adjusted CLI option parsing and added tests.

#### 🔧 **Improvements in v0.16.0** (if any)

- Refactor: Apply review fixes to AI and Git helpers.
- Refactor: AI client cleanup and dependency updates.

#### 📝 **Key Commits in v0.16.0**

`778e045`, `bc6cbeb`, `08304d4`, `2990555`, `01a0ec3`

---

## **v0.15.1** - *July 2024*

**🐛 Fixed -a flag logic, minor enhancements**

### 🐛 **Bug Fixes**

- **Fixed**: Errors related to the -a flag logic

### 📝 **Commits**: `2867f4f`, `11f82ce`, `7fae0d1`, `44de6f1`, `3f7b6d4`

---
