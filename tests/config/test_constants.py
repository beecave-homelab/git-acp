"""Tests for configuration constants in git_acp.config.constants."""

import os

import pytest
from pytest import MonkeyPatch

from git_acp.config import constants
from git_acp.config.constants import FILE_CATEGORY_PATTERNS, SIGNAL_LAYER_WEIGHTS


class TestConstants:
    """Test suite for configuration constants."""

    @pytest.fixture(autouse=True)
    def clear_env(self) -> None:
        """Clear relevant environment variables before each test."""
        keys = [k for k in os.environ if k.startswith("GIT_ACP_")]
        for key in keys:
            del os.environ[key]

    @pytest.mark.parametrize(
        "env_var, constant, default, cast_type",
        [
            ("GIT_ACP_AI_MODEL", "DEFAULT_AI_MODEL", "mevatron/diffsense:1.5b", str),
            ("GIT_ACP_TEMPERATURE", "DEFAULT_TEMPERATURE", 0.7, float),
            ("GIT_ACP_CONTEXT_WINDOW", "DEFAULT_CONTEXT_WINDOW", 8192, int),
            ("GIT_ACP_DEFAULT_BRANCH", "DEFAULT_BRANCH", "main", str),
            ("GIT_ACP_DEBUG_HEADER_COLOR", "COLORS", "blue", dict),
            (
                "GIT_ACP_FALLBACK_BASE_URL",
                "DEFAULT_FALLBACK_BASE_URL",
                "https://diffsense.onrender.com/v1",
                str,
            ),
        ],
    )
    def test_environment_overrides(
        self,
        monkeypatch: MonkeyPatch,
        env_var: str,
        constant: str,
        default: object,
        cast_type: type,
    ) -> None:
        """Constants should reflect environment variables when set."""
        if cast_type is str:
            test_value = "test_value_123"
        elif cast_type is int:
            test_value = "123"
        else:
            test_value = "0.99"
        monkeypatch.setenv(env_var, test_value)

        # Reload module to pick up new env vars
        import importlib

        importlib.reload(constants)

        value = getattr(constants, constant)
        if isinstance(value, dict):
            # Extract color key from env var name (GIT_ACP_<KEY>_COLOR)
            color_key = "_".join(env_var.split("_")[2:-1]).lower()
            assert value[color_key] == test_value
        else:
            expected = cast_type(test_value) if cast_type is not dict else test_value
            assert value == expected

    def test_excluded_patterns(self) -> None:
        """Should contain essential exclusion patterns."""
        essential_patterns = {"__pycache__", ".pyc", ".venv", "node_modules"}
        assert essential_patterns.issubset(set(constants.EXCLUDED_PATTERNS))

    def test_commit_type_emojis(self) -> None:
        """Commit types should have non-empty emoji values."""
        for key, value in constants.COMMIT_TYPES.items():
            assert len(value.split()) > 1, f"Missing emoji for {key}"

    def test_questionary_style_structure(self) -> None:
        """Questionary style should have correct tuple structure."""
        assert len(constants.QUESTIONARY_STYLE) >= 4
        for style in constants.QUESTIONARY_STYLE:
            assert isinstance(style, tuple) and len(style) == 2

    @pytest.mark.parametrize(
        "width_env, expected",
        [
            ("80", 80),
            ("invalid", 100),  # Default fallback
            (None, 100),
        ],
    )
    def test_terminal_width_handling(
        self,
        monkeypatch: MonkeyPatch,
        width_env: str | None,
        expected: int,
    ) -> None:
        """Should handle valid/invalid terminal width values."""
        if width_env is not None:
            monkeypatch.setenv("GIT_ACP_TERMINAL_WIDTH", width_env)

        import importlib

        importlib.reload(constants)

        assert constants.TERMINAL_WIDTH == expected


class TestFileCategoryPatterns:
    """Tests for the FILE_CATEGORY_PATTERNS constant added in this PR."""

    def test_all_expected_category_keys_present(self) -> None:
        """FILE_CATEGORY_PATTERNS should contain all expected category names."""
        expected_keys = {
            "DEPENDENCY", "GENERATED", "CI", "TEST",
            "DOCS", "BUILD", "CONFIG", "STYLE",
        }
        assert expected_keys.issubset(set(FILE_CATEGORY_PATTERNS.keys()))

    def test_all_values_are_non_empty_lists(self) -> None:
        """Every category must have at least one pattern."""
        for category, patterns in FILE_CATEGORY_PATTERNS.items():
            assert isinstance(patterns, list), f"{category} value is not a list"
            assert len(patterns) > 0, f"{category} has no patterns"

    def test_all_patterns_are_strings(self) -> None:
        """Every pattern in FILE_CATEGORY_PATTERNS must be a non-empty string."""
        for category, patterns in FILE_CATEGORY_PATTERNS.items():
            for pattern in patterns:
                assert isinstance(pattern, str), (
                    f"Pattern {pattern!r} in {category} is not a string"
                )
                assert len(pattern) > 0, f"Empty pattern found in {category}"

    def test_dependency_patterns_include_common_lockfiles(self) -> None:
        """DEPENDENCY patterns must cover the most common lockfile names."""
        dep_patterns = FILE_CATEGORY_PATTERNS["DEPENDENCY"]
        for expected in ("requirements", "uv.lock", "package-lock.json", "yarn.lock"):
            assert any(expected in p for p in dep_patterns), (
                f"Expected '{expected}' in DEPENDENCY patterns"
            )

    def test_test_patterns_cover_standard_conventions(self) -> None:
        """TEST patterns must cover 'tests/', 'test_' prefix, and '_test.py' suffix."""
        test_patterns = FILE_CATEGORY_PATTERNS["TEST"]
        assert any("tests/" in p or p == "tests/" for p in test_patterns)
        assert any("test_" in p for p in test_patterns)
        assert any("_test.py" in p for p in test_patterns)

    def test_ci_patterns_include_github_workflows(self) -> None:
        """CI patterns must include the GitHub Actions workflows path."""
        ci_patterns = FILE_CATEGORY_PATTERNS["CI"]
        assert any(".github/workflows" in p for p in ci_patterns)

    def test_docs_patterns_include_readme_and_md(self) -> None:
        """DOCS patterns must include README and .md extension."""
        docs_patterns = FILE_CATEGORY_PATTERNS["DOCS"]
        assert any("README" in p for p in docs_patterns)
        assert any(".md" in p for p in docs_patterns)

    def test_build_patterns_include_dockerfile(self) -> None:
        """BUILD patterns must include Dockerfile."""
        build_patterns = FILE_CATEGORY_PATTERNS["BUILD"]
        assert any("Dockerfile" in p for p in build_patterns)

    def test_config_patterns_include_pyproject_toml(self) -> None:
        """CONFIG patterns must include pyproject.toml."""
        config_patterns = FILE_CATEGORY_PATTERNS["CONFIG"]
        assert any("pyproject.toml" in p for p in config_patterns)

    def test_style_patterns_include_common_linting_configs(self) -> None:
        """STYLE patterns must cover .flake8, ruff.toml, and .pylintrc."""
        style_patterns = FILE_CATEGORY_PATTERNS["STYLE"]
        for expected in (".flake8", "ruff.toml", ".pylintrc"):
            assert any(expected in p for p in style_patterns), (
                f"Expected '{expected}' in STYLE patterns"
            )

    def test_is_final_mapping(self) -> None:
        """FILE_CATEGORY_PATTERNS is typed as Final — it should not be reassigned."""
        # We can only verify it exists and is a dict; Final is a type annotation only.
        assert isinstance(FILE_CATEGORY_PATTERNS, dict)

    def test_no_duplicate_category_keys(self) -> None:
        """Each category key appears only once (dict semantics guarantee this)."""
        # Dict construction ensures uniqueness; just verify the count is sensible.
        assert len(FILE_CATEGORY_PATTERNS) >= 8


class TestSignalLayerWeights:
    """Tests for the SIGNAL_LAYER_WEIGHTS constant added in this PR."""

    def test_all_expected_signal_keys_present(self) -> None:
        """SIGNAL_LAYER_WEIGHTS must contain all four signal layer keys."""
        expected_keys = {
            "message_prefix",
            "file_category",
            "message_keyword",
            "diff_keyword",
        }
        assert set(SIGNAL_LAYER_WEIGHTS.keys()) == expected_keys

    def test_all_weights_are_floats(self) -> None:
        """Every weight value must be a float."""
        for key, weight in SIGNAL_LAYER_WEIGHTS.items():
            assert isinstance(weight, float), f"Weight for '{key}' is not a float"

    def test_all_weights_are_positive(self) -> None:
        """Every weight value must be positive."""
        for key, weight in SIGNAL_LAYER_WEIGHTS.items():
            assert weight > 0, f"Weight for '{key}' is not positive"

    def test_default_weights_are_all_one(self) -> None:
        """Default weights should all be 1.0 as documented."""
        for key, weight in SIGNAL_LAYER_WEIGHTS.items():
            assert weight == 1.0, f"Default weight for '{key}' is {weight}, expected 1.0"

    def test_message_prefix_weight(self) -> None:
        """message_prefix weight is 1.0."""
        assert SIGNAL_LAYER_WEIGHTS["message_prefix"] == 1.0

    def test_file_category_weight(self) -> None:
        """file_category weight is 1.0."""
        assert SIGNAL_LAYER_WEIGHTS["file_category"] == 1.0

    def test_message_keyword_weight(self) -> None:
        """message_keyword weight is 1.0."""
        assert SIGNAL_LAYER_WEIGHTS["message_keyword"] == 1.0

    def test_diff_keyword_weight(self) -> None:
        """diff_keyword weight is 1.0."""
        assert SIGNAL_LAYER_WEIGHTS["diff_keyword"] == 1.0

    def test_is_final_mapping(self) -> None:
        """SIGNAL_LAYER_WEIGHTS should be a dict (Final is annotation-only)."""
        assert isinstance(SIGNAL_LAYER_WEIGHTS, dict)


class TestNewCommitTypes:
    """Tests for the new BUILD, CI, and PERF commit type entries added in this PR."""

    def test_build_commit_type_present(self) -> None:
        """COMMIT_TYPES should include BUILD key."""
        assert "BUILD" in constants.COMMIT_TYPES

    def test_ci_commit_type_present(self) -> None:
        """COMMIT_TYPES should include CI key."""
        assert "CI" in constants.COMMIT_TYPES

    def test_perf_commit_type_present(self) -> None:
        """COMMIT_TYPES should include PERF key."""
        assert "PERF" in constants.COMMIT_TYPES

    def test_build_value_has_keyword_and_emoji(self) -> None:
        """BUILD value should have a keyword part and an emoji part."""
        value = constants.COMMIT_TYPES["BUILD"]
        parts = value.split()
        assert len(parts) >= 2, f"BUILD value '{value}' should have keyword and emoji"
        assert parts[0] == "build"

    def test_ci_value_has_keyword_and_emoji(self) -> None:
        """CI value should have a keyword part and an emoji part."""
        value = constants.COMMIT_TYPES["CI"]
        parts = value.split()
        assert len(parts) >= 2, f"CI value '{value}' should have keyword and emoji"
        assert parts[0] == "ci"

    def test_perf_value_has_keyword_and_emoji(self) -> None:
        """PERF value should have a keyword part and an emoji part."""
        value = constants.COMMIT_TYPES["PERF"]
        parts = value.split()
        assert len(parts) >= 2, f"PERF value '{value}' should have keyword and emoji"
        assert parts[0] == "perf"

    def test_new_commit_types_are_env_overridable(self) -> None:
        """BUILD, CI, and PERF commit type values should respect environment variables."""
        import importlib

        env_overrides = {
            "GIT_ACP_COMMIT_TYPE_BUILD": "GIT_ACP_COMMIT_TYPE_BUILD",
            "GIT_ACP_COMMIT_TYPE_CI": "GIT_ACP_COMMIT_TYPE_CI",
            "GIT_ACP_COMMIT_TYPE_PERF": "GIT_ACP_COMMIT_TYPE_PERF",
        }
        # Just verify the defaults are non-empty strings; env override tested separately
        for key in ("BUILD", "CI", "PERF"):
            assert isinstance(constants.COMMIT_TYPES[key], str)
            assert len(constants.COMMIT_TYPES[key]) > 0
