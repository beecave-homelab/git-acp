"""Unit tests for type definitions and dataclasses."""

from git_acp.utils.types import CommitDict, DiffType, GitConfig, PromptType


def test_gitconfig_default_values() -> None:
    """Test GitConfig dataclass default values."""
    config = GitConfig()
    assert config.files == "."
    assert config.message == "Automated commit"
    assert config.use_ollama is False
    assert config.interactive is False
    assert config.prompt_type == "advanced"
    assert config.prompt is None
    assert config.ai_model is None
    assert config.context_window is None


def test_gitconfig_custom_values() -> None:
    """Test GitConfig initialization with custom values."""
    custom_config = GitConfig(
        files="src/",
        message="Custom message",
        use_ollama=True,
        interactive=True,
        prompt="Write a commit message.",
        prompt_type="simple",
        ai_model="example/model:latest",
        context_window=4096,
    )
    assert custom_config.files == "src/"
    assert custom_config.message == "Custom message"
    assert custom_config.use_ollama is True
    assert custom_config.interactive is True
    assert custom_config.prompt == "Write a commit message."
    assert custom_config.prompt_type == "simple"
    assert custom_config.ai_model == "example/model:latest"
    assert custom_config.context_window == 4096


def test_diff_type_literal() -> None:
    """Test DiffType literal values."""
    valid_values = DiffType.__args__  # type: ignore
    assert "staged" in valid_values
    assert "unstaged" in valid_values
    assert len(valid_values) == 2


def test_prompt_type_literal() -> None:
    """Test PromptType literal values."""
    valid_values = PromptType.__args__  # type: ignore
    assert "simple" in valid_values
    assert "advanced" in valid_values
    assert len(valid_values) == 2


def test_commit_dict_type() -> None:
    """Test CommitDict type definition."""
    sample_commit: CommitDict = {
        "hash": "abc123",
        "message": "Initial commit",
        "author": "Dev",
    }
    assert isinstance(sample_commit, dict)
    assert all(isinstance(k, str) for k in sample_commit.keys())
    assert all(isinstance(v, str) for v in sample_commit.values())


def test_gitconfig_type_annotations() -> None:
    """Test type annotations for GitConfig fields."""
    annotations = GitConfig.__annotations__
    assert annotations["files"] is str
    assert annotations["message"] is str

    # Accept both old-style (typing.Optional) and new-style (X | None) representations
    branch_annotation = str(annotations["branch"])
    assert "str" in branch_annotation
    assert "None" in branch_annotation or "Optional" in branch_annotation

    assert annotations["use_ollama"] is bool
    assert annotations["interactive"] is bool
    assert annotations["prompt_type"] is str


def test_config_serialization() -> None:
    """Test dataclass serialization capabilities."""
    config = GitConfig(skip_confirmation=True)
    config_dict = {
        "files": ".",
        "message": "Automated commit",
        "branch": None,
        "use_ollama": False,
        "interactive": False,
        "skip_confirmation": True,
        "verbose": False,
        "prompt_type": "advanced",
        "prompt": None,
        "ai_model": None,
        "context_window": None,
    }
    assert vars(config) == config_dict
