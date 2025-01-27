# API Overview

This section provides a comprehensive overview of the `git-acp` package's API and its components.

## CLI Module

### Main Command Interface

The main command interface is provided through the `git-acp` command with the following options:

```bash
git-acp [OPTIONS]
```

#### Git Operations Options
- `-a, --add <file>`: Specify files to stage for commit
- `-m, --message <message>`: Custom commit message
- `-b, --branch <branch>`: Target branch for push operation
- `-t, --type <type>`: Manually specify commit type

#### AI Features Options
- `-o, --ollama`: Use Ollama AI for commit message generation
- `-i, --interactive`: Enable interactive AI message editing
- `-p, --prompt-type <type>`: Select AI prompt complexity (simple/advanced)

#### General Options
- `-nc, --no-confirm`: Skip confirmation prompts
- `-v, --verbose`: Enable verbose debug output

## Git Module

### Core Operations

#### File Management
- `git_add(files: str) -> None`: Add files to staging area
- `git_commit(message: str) -> None`: Commit staged changes
- `git_push(branch: str) -> None`: Push commits to remote

#### Branch Operations
- `get_current_branch() -> str`: Get current branch name
- `create_branch(branch_name: str) -> None`: Create new branch
- `delete_branch(branch_name: str, force: bool = False) -> None`: Delete branch
- `merge_branch(source_branch: str) -> None`: Merge branch into current

#### Repository Analysis
- `get_changed_files() -> Set[str]`: Get modified files
- `get_diff(diff_type: str = "staged") -> str`: Get diff output
- `get_recent_commits(num_commits: int = 3) -> List[Dict]`: Get commit history

## AI Module

### Commit Message Generation

#### Main Functions
- `generate_commit_message(config: GitConfig) -> str`: Generate AI commit message
- `edit_commit_message(message: str, config: GitConfig) -> str`: Edit generated message

#### Context Analysis
- `get_commit_context(config: GitConfig) -> Dict`: Gather repository context
- `analyze_commit_patterns(commits: List[Dict]) -> Dict`: Analyze commit history

## Configuration

### Environment Variables

#### AI Configuration
- `GIT_ACP_AI_MODEL`: Ollama model name
- `GIT_ACP_TEMPERATURE`: AI generation temperature
- `GIT_ACP_BASE_URL`: Ollama API endpoint
- `GIT_ACP_PROMPT_TYPE`: Prompt complexity type

#### Git Configuration
- `GIT_ACP_DEFAULT_BRANCH`: Default branch name
- `GIT_ACP_DEFAULT_REMOTE`: Default remote name
- `GIT_ACP_NUM_RECENT_COMMITS`: Number of commits to analyze

#### Terminal Configuration
- `GIT_ACP_TERMINAL_WIDTH`: Output width
- Various color configuration options

## Error Handling

The package uses the custom `GitError` exception class for error handling, providing:
- Descriptive error messages
- Context-specific error information
- User-friendly suggestions for resolution

## Type Definitions

### Custom Types
- `CommitType`: Enum for conventional commit types
- `GitConfig`: Configuration settings container
- `DiffType`: Type for diff operations ("staged"/"unstaged") 