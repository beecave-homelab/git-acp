# Advanced Usage

This guide covers advanced features and configurations of `git-acp` for power users.

## AI Configuration

### Customizing Ollama Integration

#### Model Selection
Configure the AI model in your environment:
```bash
export GIT_ACP_AI_MODEL="mevatron/diffsense:1.5b"
```

#### Temperature Control
Adjust AI creativity (0.0-1.0):
```bash
export GIT_ACP_TEMPERATURE="0.7"
```

#### API Configuration
```bash
export GIT_ACP_BASE_URL="http://localhost:11434/v1"
export GIT_ACP_API_KEY="ollama"
```

### Advanced Prompt Types

#### Simple Mode
Basic commit message generation:
```bash
git-acp -o -p simple
```

#### Advanced Mode
Context-aware generation with repository analysis:
```bash
git-acp -o -p advanced
```

## Git Operations

### Branch Management

#### Creating Feature Branches
```bash
git-acp -b feature/new-feature -t feat -o
```

#### Handling Merge Conflicts
```bash
# After resolving conflicts
git-acp -m "Merge conflict resolution" -t fix
```

### Remote Operations

#### Multiple Remotes
```bash
# Configure default remote
export GIT_ACP_DEFAULT_REMOTE="upstream"
```

#### Push Behavior
```bash
# Force push (use with caution)
git push -f && git-acp
```

## Terminal Customization

### Output Formatting

#### Terminal Width
```bash
export GIT_ACP_TERMINAL_WIDTH="120"
```

#### Color Configuration
```bash
export GIT_ACP_SUCCESS_COLOR="green"
export GIT_ACP_WARNING_COLOR="yellow"
export GIT_ACP_ERROR_COLOR="bold red"
```

### Debug Output

#### Verbose Logging
```bash
git-acp -v
```

#### Debug Information
```bash
# Show all debug info
export GIT_ACP_DEBUG=1
```

## Commit Analysis

### History Analysis

#### Recent Commits
Configure number of commits to analyze:
```bash
export GIT_ACP_NUM_RECENT_COMMITS="5"
```

#### Related Commits
```bash
export GIT_ACP_NUM_RELATED_COMMITS="3"
```

### Pattern Recognition

#### Custom Commit Types
Define custom commit type patterns:
```bash
export GIT_ACP_COMMIT_TYPE_FEAT="feat ✨"
export GIT_ACP_COMMIT_TYPE_FIX="fix 🐛"
```

## Environment Configuration

### Configuration File
Create `.env` in `~/.config/git-acp/`:

```ini
# AI Configuration
GIT_ACP_AI_MODEL=mevatron/diffsense:1.5b
GIT_ACP_TEMPERATURE=0.7

# Git Configuration
GIT_ACP_DEFAULT_BRANCH=main
GIT_ACP_DEFAULT_REMOTE=origin

# Terminal Configuration
GIT_ACP_TERMINAL_WIDTH=100
GIT_ACP_DEBUG_HEADER_COLOR=blue
```

### Multiple Configurations
Use different configurations for different projects:

```bash
# Project-specific configuration
source .env.project
git-acp
```

## Advanced Use Cases

### CI/CD Integration

#### Automated Commits
```bash
git-acp -nc -m "CI: Update dependencies" -t chore
```

#### Version Bumping
```bash
git-acp -a "version.txt" -m "chore(release): bump version to v1.0.0" -t chore
```

### Batch Operations

#### Multiple File Types
```bash
git-acp -a "*.py src/*.js tests/*.py" -t refactor -o
```

#### Complex Patterns
```bash
git-acp -a "src/**/*.{js,ts} !src/vendor/*" -t feat
```

## Performance Optimization

### Commit Analysis
- Limit recent commits analysis
- Use simple prompt type for faster generation
- Skip confirmations when appropriate

### AI Generation
- Adjust temperature for faster responses
- Use local Ollama instance
- Cache common commit patterns

## Troubleshooting

### Common Issues

#### AI Connection
```bash
# Check Ollama server
curl http://localhost:11434/v1/health
```

#### Git Issues
```bash
# Reset state
git reset HEAD && git-acp
```

### Debug Mode
Enable full debug output:
```bash
git-acp -v
``` 