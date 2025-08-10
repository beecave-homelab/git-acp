import os
import pytest
from git_acp.config import constants


class TestConstants:
    """Test suite for configuration constants"""

    @pytest.fixture(autouse=True)
    def clear_env(self):
        """Clear relevant environment variables before each test"""
        keys = [k for k in os.environ if k.startswith("GIT_ACP_")]
        for key in keys:
            del os.environ[key]

    @pytest.mark.parametrize(
        "env_var, constant, default, cast_type",
        [
            ("GIT_ACP_AI_MODEL", "DEFAULT_AI_MODEL", "mevatron/diffsense:1.5b", str),
            ("GIT_ACP_TEMPERATURE", "DEFAULT_TEMPERATURE", 0.7, float),
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
        self, monkeypatch, env_var, constant, default, cast_type
    ):
        """Constants should reflect environment variables when set"""
        test_value = "test_value_123" if cast_type == str else "0.99"
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
            expected = cast_type(test_value) if cast_type != dict else test_value
            assert value == expected

    def test_excluded_patterns(self):
        """Should contain essential exclusion patterns"""
        essential_patterns = {"__pycache__", ".pyc", ".venv", "node_modules"}
        assert essential_patterns.issubset(set(constants.EXCLUDED_PATTERNS))

    def test_commit_type_emojis(self):
        """Commit types should have non-empty emoji values"""
        for key, value in constants.COMMIT_TYPES.items():
            assert len(value.split()) > 1, f"Missing emoji for {key}"

    def test_questionary_style_structure(self):
        """Questionary style should have correct tuple structure"""
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
    def test_terminal_width_handling(self, monkeypatch, width_env, expected):
        """Should handle valid/invalid terminal width values"""
        if width_env is not None:
            monkeypatch.setenv("GIT_ACP_TERMINAL_WIDTH", width_env)

        import importlib

        importlib.reload(constants)

        assert constants.TERMINAL_WIDTH == expected
