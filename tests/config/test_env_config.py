"""Tests for git_acp.config.env_config module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from git_acp.config.env_config import (
    ensure_config_dir,
    get_config_dir,
    get_env,
    load_env_config,
)


class TestEnvConfig:
    """Test suite for environment configuration handling."""

    @patch("pathlib.Path.home")
    def test_get_config_dir(self, mock_home):
        """Should return correct config directory path."""
        mock_home.return_value = Path("/test/home")
        assert get_config_dir() == Path("/test/home/.config/git-acp")

    @patch("pathlib.Path.mkdir")
    def test_ensure_config_dir_creation(self, mock_mkdir):
        """Should create directory with parents if not exists."""
        ensure_config_dir()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("git_acp.config.env_config.load_dotenv")
    def test_load_env_config_with_existing_file(self, mock_load):
        """Should load .env file when present."""
        with (
            patch.dict(os.environ, {"GIT_ACP_ALLOW_TEST_ENV_LOAD": "1"}),
            patch("pathlib.Path.exists", return_value=True),
        ):
            load_env_config()

        mock_load.assert_called_once_with(get_config_dir() / ".env")

    @patch("git_acp.config.env_config.load_dotenv")
    def test_load_env_config_missing_file(self, mock_load):
        """Should not attempt load when .env missing."""
        with (
            patch.dict(os.environ, {"GIT_ACP_ALLOW_TEST_ENV_LOAD": "1"}),
            patch("pathlib.Path.exists", return_value=False),
        ):
            load_env_config()

        mock_load.assert_not_called()

    @pytest.mark.parametrize(
        "env_value, cast_type, expected",
        [
            ("123", int, 123),
            ("45.67", float, 45.67),
            ("true", bool, True),
            ("False", bool, False),
            ("invalid", int, None),
        ],
    )
    def test_get_env_type_casting(self, monkeypatch, env_value, cast_type, expected):
        """Should correctly cast environment values to specified types."""
        monkeypatch.setenv("TEST_KEY", env_value)
        result = get_env("TEST_KEY", default=None, type_cast=cast_type)
        assert result == expected or (result is None and expected is None)

    def test_get_env_fallback_default(self):
        """Should return default when env var not set."""
        assert get_env("NON_EXISTENT_KEY", default="fallback") == "fallback"

    def test_bool_casting_edge_cases(self):
        """Should handle various boolean representations."""
        for val in ["1", "yes", "Y", "True"]:
            assert get_env("TEST_BOOL", val, bool) is True
        for val in ["0", "no", "n", "false"]:
            assert get_env("TEST_BOOL", val, bool) is False
