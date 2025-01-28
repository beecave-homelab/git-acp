# Basic Usage

This guide covers the fundamental usage patterns of `git-acp` for common Git workflows.

## Command-Line Usage

### Basic Commit Flow

The simplest way to use `git-acp` is without any options, which launches interactive mode:

```bash
git-acp
```

This will:

1. Show status of changed files
2. Present a selection menu for staging files
3. Suggest a commit type based on changes
4. Generate or prompt for a commit message
5. Show a preview and confirmation before pushing

### Command Options

The tool provides several options grouped into three categories:

#### Git Operations

- `-a, --add <file>`: Specify files to stage for commit. Shows interactive selection if omitted
- `-m, --message <message>`: Custom commit message (defaults to 'Automated commit' without --ollama)
- `-b, --branch <branch>`: Target branch for push operation
- `-t, --type <type>`: Manually specify the commit type

#### AI Features

- `-o, --ollama`: Use Ollama AI to generate descriptive commit messages
- `-i, --interactive`: Review and edit AI-generated messages (requires --ollama)
- `-p, --prompt-type <type>`: Select AI prompt complexity ('simple' or 'advanced')

#### General Options

- `-nc, --no-confirm`: Skip all confirmation prompts
- `-v, --verbose`: Enable detailed debug output

### Quick Commit with Message

To quickly commit specific files with a message:

```bash
git-acp -a "README.md docs/*" -m "Update documentation"
```

### Using AI-Generated Messages

To use Ollama AI for generating commit messages:

```bash
git-acp -o
```

For interactive AI message editing:

```bash
git-acp -o -i
```

### Specifying Branch and Type

To commit and push to a specific branch with a commit type:

```bash
git-acp -b feature/new-branch -t feat
```

## Common Use Cases

### 1. Documentation Updates

```bash
git-acp -a "docs/*" -t docs -m "Update installation instructions"
```

### 2. Bug Fixes

```bash
git-acp -a "src/bugfix.py" -t fix -o
```

### 3. Feature Development

```bash
git-acp -a "src/features/*" -t feat -o -i
```

### 4. Quick Fixes

```bash
git-acp -nc -m "Quick fix" -a .
```

### 5. Style Changes

```bash
git-acp -a "*.css" -t style -m "Update button styles"
```

## File Selection

### Interactive Selection

- Use space to select/deselect files
- Enter to confirm selection
- Arrow keys to navigate
- Select "All files" to stage everything

### Pattern Matching

- Use wildcards: `*.py`, `src/**/*.js`
- Multiple patterns: `"*.md" "src/*.py"`
- Exclude patterns: `"src/*" "!src/test/*"`

## Commit Messages

### Manual Messages

- Keep messages concise but descriptive
- Follow conventional commits format
- Include scope if relevant

### AI-Generated Messages

- Use `-o` for AI generation
- `-i` allows editing before commit
- Choose prompt type with `-p`

## Confirmation and Safety

### Confirmation Prompts

- Review changes before commit
- Confirm commit message
- Verify push operation

### Skip Confirmations

Use `-nc` to skip all confirmations:

```bash
git-acp -nc -a . -m "Quick update"
```

## Error Handling

The tool provides clear error messages for common issues:

- Repository not found
- Nothing to commit
- Push conflicts
- Permission issues
- Remote access errors

## Getting Help

For command help and options:

```bash
git-acp --help
```

For verbose output and debugging:

```bash
git-acp -v
```
