# Advanced Usage

This guide covers advanced features and configurations of `git-acp` for power users.

## Configuration

### Setting Up Configuration File

Create a `.env` file in `~/.config/git-acp/` directory:

```bash
mkdir -p ~/.config/git-acp/
cp .env.example ~/.config/git-acp/.env
```

Then edit the `.env` file to customize your settings.

### AI Configuration

#### Model Selection

The AI model selection determines which model will be used for generating commit messages. Different models have different capabilities, sizes, and performance characteristics. The default model `mevatron/diffsense:1.5b` is optimized for understanding code changes and generating relevant commit messages.

**Tested Models:**

- `mevatron/diffsense:0.5b`
- `mevatron/diffsense:1.5b`
- `tavernari/git-commit-message:latest`

In your `~/.config/git-acp/.env` file:

```env
# AI model configuration
GIT_ACP_AI_MODEL=mevatron/diffsense:1.5b
```

#### Temperature Control

In AI models, the temperature setting (ranging from 0.0 to 1.0) controls the randomness of the output. Lower values (e.g., 0.1) make the model's output more deterministic and focused, often producing more conventional commit messages. Higher values (e.g., 0.9) make the output more diverse and creative, potentially generating more unique but less conventional messages.

```env
# Temperature for generation
GIT_ACP_TEMPERATURE=0.7
```

#### API Configuration

`git-acp` supports various AI integrations that follow the OpenAI API standards. While Ollama is the preferred integration due to its ability to run models offline and locally, you can configure any compatible AI service:

- **Ollama (Default)**: Run AI models locally without internet connection
- **Local-AI**: Another option for local AI model hosting
- **OpenAI**: Cloud-based service with GPT models
- **Anthropic**: Cloud-based service with Claude models

The base URL and API key settings allow you to configure your preferred AI service. You can also set a fallback base URL that will be used if the primary service is unavailable. For local installations using Ollama, the default values are typically sufficient.

```env
# Ollama API settings (default)
GIT_ACP_BASE_URL=http://localhost:11434/v1
GIT_ACP_FALLBACK_BASE_URL=https://diffsense.onrender.com/v1
GIT_ACP_API_KEY=ollama

# Example for OpenAI
# GIT_ACP_BASE_URL=https://api.openai.com/v1
# GIT_ACP_API_KEY=your-openai-api-key

# Example for Anthropic
# GIT_ACP_BASE_URL=https://api.anthropic.com/v1
# GIT_ACP_API_KEY=your-anthropic-api-key

# Example for Local-AI
# GIT_ACP_BASE_URL=http://localhost:8080/v1
# GIT_ACP_API_KEY=your-local-ai-key
```

Note: When using cloud-based services like OpenAI or Anthropic, you'll need an active internet connection and valid API credentials. Local solutions like Ollama or Local-AI allow for offline operation but require local system resources to run the models.

#### Prompt Type and Timeout

The prompt type determines how the AI generates commit messages. There are two available modes:

##### Simple Mode (`simple`)

Simple mode focuses solely on the current changes, generating straightforward commit messages without additional context. This mode is faster and suitable for simple changes or when repository context isn't necessary.

Example prompt generated in simple mode:

```markdown
Generate a concise and descriptive commit message for the following changes:

Changes to commit:
<staged changes from git status>
```

Example output will be a conventional commit message based on the actual changes.

##### Advanced Mode (`advanced`)

Advanced mode provides the AI with rich repository context, including:

- Analysis of recent commit patterns
- Most commonly used commit types
- Recent commit history
- Related commits for similar changes

This mode generates more contextually aware messages that maintain consistency with your repository's commit style.

Example prompt generated in advanced mode:

```markdown
Generate a concise and descriptive commit message for the following changes:

Changes to commit:
<staged changes from git status>

Repository context:
- Most used commit type: <most frequent commit type from recent history>
- Recent commits:
<list of recent commit messages>

Related commits:
<list of semantically related commit messages>

Requirements:
1. Follow the repository's commit style (type: description)
2. Be specific about what changed and why
3. Reference related work if relevant
4. Keep it concise but descriptive
```

Example output will be a conventional commit message that takes into account the repository's commit history and patterns.

The timeout setting (`GIT_ACP_AI_TIMEOUT`) controls how long to wait for AI responses before timing out. The default value of 120.0 seconds is suitable for most use cases, but you may want to adjust it based on your AI provider's response times.

```env
# AI generation settings
GIT_ACP_PROMPT_TYPE=simple  # or 'advanced' for more context
GIT_ACP_AI_TIMEOUT=120.0    # timeout in seconds
GIT_ACP_CONTEXT_WINDOW=8192 # context window size in tokens for Ollama requests
```

### Per-Run CLI Overrides

You can override AI settings for individual runs without modifying your configuration file:

- `--model <model>`: Override the AI model for this run (e.g., `--model granite4:latest`)
- `--context-window <tokens>`: Override the context window size for this run (e.g., `--context-window 4096`)
- `--prompt <prompt>`: Provide a custom prompt that replaces the built-in templates for this run

Example usage:

```bash
# Use a different model with larger context for a complex change
git-acp -o --model granite4:latest --context-window 16384

# Use a custom prompt for specific commit style
git-acp -o --prompt "Generate a commit message in the format: type(scope): description"

# Combine overrides
git-acp -o --model llama3.2:latest --context-window 4096 --prompt "Generate a concise commit message focusing on the 'why' rather than the 'what'"
```

These flags take precedence over environment variables and defaults for the current invocation only.

## Git Configuration

### Branch and Remote Settings

These settings define the default Git branch and remote repository for operations. They're particularly useful in automated workflows or when working with multiple remotes.

```env
# Git defaults
GIT_ACP_DEFAULT_BRANCH=main
GIT_ACP_DEFAULT_REMOTE=origin
```

### History Analysis

These settings control how many commits the tool analyzes when generating context-aware commit messages in advanced prompt mode (`GIT_ACP_PROMPT_TYPE=advanced`). They determine the amount of repository context provided to the AI:

- `GIT_ACP_NUM_RECENT_COMMITS`: Number of most recent commits to include in the "Recent commits" section of the advanced prompt
- `GIT_ACP_NUM_RELATED_COMMITS`: Number of semantically related commits to include in the "Related commits" section
- `GIT_ACP_MAX_DIFF_PREVIEW_LINES`: Maximum number of diff lines to show in the changes preview

These settings only affect the advanced prompt type and are ignored when using simple mode.

```env
# Analysis settings
GIT_ACP_NUM_RECENT_COMMITS=3
GIT_ACP_NUM_RELATED_COMMITS=3
GIT_ACP_MAX_DIFF_PREVIEW_LINES=10
```

**Note:** Higher values provide more context but may increase processing time and token usage with your AI provider. When increasing these values, consider the cost implications and adjust the `GIT_ACP_AI_TIMEOUT` setting accordingly.

## Terminal Configuration

### Color Settings

These settings control the appearance of different message types in the terminal output. Rich color names are supported to help distinguish between different types of information.

```env
# Terminal Colors
GIT_ACP_DEBUG_HEADER_COLOR=blue
GIT_ACP_DEBUG_VALUE_COLOR=cyan
GIT_ACP_SUCCESS_COLOR=green
GIT_ACP_WARNING_COLOR=yellow
GIT_ACP_STATUS_COLOR=bold green
GIT_ACP_ERROR_COLOR=bold red
GIT_ACP_AI_MESSAGE_HEADER_COLOR=bold yellow
GIT_ACP_AI_MESSAGE_BORDER_COLOR=yellow
GIT_ACP_KEY_COMBINATION_COLOR=cyan
GIT_ACP_INSTRUCTION_TEXT_COLOR=dim
GIT_ACP_BOLD_COLOR=dim

# Terminal width
GIT_ACP_TERMINAL_WIDTH=100
```

### Commit Types

These settings define the commit type prefixes and their associated emojis, following the Conventional Commits specification.

```env
# Commit type configuration
GIT_ACP_COMMIT_TYPE_FEAT="feat ✨"
GIT_ACP_COMMIT_TYPE_FIX="fix 🐛"
GIT_ACP_COMMIT_TYPE_DOCS="docs 📝"
GIT_ACP_COMMIT_TYPE_STYLE="style 💎"
GIT_ACP_COMMIT_TYPE_REFACTOR="refactor ♻️"
GIT_ACP_COMMIT_TYPE_TEST="test 🧪"
GIT_ACP_COMMIT_TYPE_CHORE="chore 📦"
GIT_ACP_COMMIT_TYPE_REVERT="revert ⏪"
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
git-acp -mb "Merge conflict resolution" -t fix
```

### Remote Operations

#### Push Behavior

```bash
# Force push (use with caution)
git push -f && git-acp
```

## Environment Configuration

### Configuration File Location

The configuration file should be placed at `~/.config/git-acp/.env`. You can use the provided `.env.example` as a template:

```bash
# Copy the example configuration
mkdir -p ~/.config/git-acp/
cp .env.example ~/.config/git-acp/.env

# Edit the configuration
nano ~/.config/git-acp/.env
```

## Advanced Use Cases

### CI/CD Integration

#### Automated Commits

```bash
git-acp -nc -mb "CI: Update dependencies" -t chore
```

#### Version Bumping

```bash
git-acp -a "version.txt" -mb "chore(release): bump version to v0.17.0" -t chore
```

### Batch Operations

#### Multiple File Types

```bash
git-acp -a "*.py src/*.js tests/*.py" -t refactor -o
```

#### Complex Patterns

```bash
git-acp -a "src/**/*.js src/**/*.ts" -t feat
```

Exclude patterns (e.g., `!src/vendor/*`) are not supported.

## Performance Optimization

### Analysis of Recent Commits

- Limit recent commits analysis by adjusting `GIT_ACP_NUM_RECENT_COMMITS`
- Use simple prompt type for faster generation
- Skip confirmations when appropriate

### AI Generation

 - Choose a smaller or faster model
 - Use a local Ollama instance
 - Lower temperature for more deterministic responses

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
