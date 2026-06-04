"""Tests for git_acp.config.env_config module."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from git_acp.config.env_config import (
    ensure_config_dir,
    get_config_dir,
    get_env,
    load_env_config,
    run_setup,
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


class TestRunSetup:
    """Test suite for the run_setup function."""

    def test_creates_config_when_none_exists(self, tmp_path):
        """Should create config file from bundled .env.example."""
        config_dir = tmp_path / ".config" / "git-acp"
        env_file = config_dir / ".env"

        mock_example = MagicMock()
        mock_example.exists.return_value = True
        mock_example.read_text.return_value = "GIT_ACP_AI_MODEL=test\n"

        mock_ref = MagicMock()
        mock_ref.__truediv__ = lambda s, o: mock_example

        with (
            patch("git_acp.config.env_config.get_config_dir", return_value=config_dir),
            patch("importlib.resources.files", return_value=mock_ref),
            patch("importlib.resources.as_file") as mock_as_file,
        ):
            mock_as_file.return_value.__enter__ = lambda s: mock_example
            mock_as_file.return_value.__exit__ = MagicMock(return_value=False)
            result = run_setup()

        assert result == 0
        assert env_file.exists()
        assert env_file.read_text(encoding="utf-8") == "GIT_ACP_AI_MODEL=test\n"

    def test_skips_when_config_exists_no_force(self, tmp_path):
        """Should not overwrite existing config without force."""
        config_dir = tmp_path / ".config" / "git-acp"
        config_dir.mkdir(parents=True)
        env_file = config_dir / ".env"
        env_file.write_text("existing content", encoding="utf-8")

        with patch("git_acp.config.env_config.get_config_dir", return_value=config_dir):
            result = run_setup(force=False)

        assert result == 0
        assert env_file.read_text(encoding="utf-8") == "existing content"

    def test_overwrites_with_force(self, tmp_path):
        """Should overwrite existing config when force=True."""
        config_dir = tmp_path / ".config" / "git-acp"
        config_dir.mkdir(parents=True)
        env_file = config_dir / ".env"
        env_file.write_text("old content", encoding="utf-8")

        mock_example = MagicMock()
        mock_example.exists.return_value = True
        mock_example.read_text.return_value = "new content\n"

        mock_ref = MagicMock()
        mock_ref.__truediv__ = lambda s, o: mock_example

        with (
            patch("git_acp.config.env_config.get_config_dir", return_value=config_dir),
            patch("importlib.resources.files", return_value=mock_ref),
            patch("importlib.resources.as_file") as mock_as_file,
        ):
            mock_as_file.return_value.__enter__ = lambda s: mock_example
            mock_as_file.return_value.__exit__ = MagicMock(return_value=False)
            result = run_setup(force=True)

        assert result == 0
        assert env_file.read_text(encoding="utf-8") == "new content\n"

    def test_returns_error_when_example_not_found(self, tmp_path):
        """Should return error code when .env.example is missing."""
        config_dir = tmp_path / ".config" / "git-acp"

        mock_example = MagicMock()
        mock_example.exists.return_value = False

        mock_ref = MagicMock()
        mock_ref.__truediv__ = lambda s, o: mock_example

        with (
            patch("git_acp.config.env_config.get_config_dir", return_value=config_dir),
            patch("importlib.resources.files", return_value=mock_ref),
            patch("importlib.resources.as_file") as mock_as_file,
        ):
            mock_as_file.return_value.__enter__ = lambda s: mock_example
            mock_as_file.return_value.__exit__ = MagicMock(return_value=False)
            result = run_setup()

        assert result == 1
