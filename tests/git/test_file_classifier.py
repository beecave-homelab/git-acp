"""Tests for git_acp.git.file_classifier module.

Covers:
- FileCategory enum
- _normalize_path_separators (internal helper)
- _match_file_path_pattern (internal helper)
- classify_file_category (public API)
- categorize_changed_files (public API)
"""

from __future__ import annotations

import pytest

from git_acp.git.file_classifier import (
    FileCategory,
    _match_file_path_pattern,
    _normalize_path_separators,
    categorize_changed_files,
    classify_file_category,
)


class TestFileCategory:
    """Tests for the FileCategory enum."""

    def test_all_expected_members_exist(self) -> None:
        """All expected FileCategory members should be present."""
        expected = {
            "PRODUCTION", "TEST", "DOCS", "CI", "BUILD",
            "CONFIG", "DEPENDENCY", "GENERATED", "STYLE", "UNKNOWN",
        }
        actual = {member.name for member in FileCategory}
        assert expected == actual

    def test_member_values_are_lowercase_strings(self) -> None:
        """FileCategory values should be lowercase strings."""
        for member in FileCategory:
            assert isinstance(member.value, str)
            assert member.value == member.value.lower()

    def test_production_value(self) -> None:
        """PRODUCTION category has the expected value string."""
        assert FileCategory.PRODUCTION.value == "production"

    def test_enum_access_by_name(self) -> None:
        """FileCategory members are accessible by name."""
        assert FileCategory["TEST"] == FileCategory.TEST
        assert FileCategory["DOCS"] == FileCategory.DOCS

    def test_enum_members_are_unique(self) -> None:
        """All FileCategory values should be distinct."""
        values = [m.value for m in FileCategory]
        assert len(values) == len(set(values))


class TestNormalizePathSeparators:
    """Tests for _normalize_path_separators."""

    def test_forward_slashes_unchanged(self) -> None:
        """Forward-slash paths are returned as-is."""
        assert _normalize_path_separators("a/b/c") == "a/b/c"

    def test_backslashes_converted(self) -> None:
        """Backslashes are replaced with forward slashes."""
        assert _normalize_path_separators("a\\b\\c") == "a/b/c"

    def test_mixed_separators(self) -> None:
        """Mixed separators are all replaced with forward slashes."""
        assert _normalize_path_separators("a\\b/c\\d") == "a/b/c/d"

    def test_consecutive_slashes_collapsed(self) -> None:
        """Multiple consecutive slashes collapse to one."""
        assert _normalize_path_separators("a//b///c") == "a/b/c"

    def test_consecutive_backslashes_collapsed(self) -> None:
        """Multiple consecutive backslashes collapse to one slash."""
        assert _normalize_path_separators("a\\\\b") == "a/b"

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert _normalize_path_separators("") == ""

    def test_root_slash(self) -> None:
        """A bare slash is preserved."""
        assert _normalize_path_separators("/") == "/"

    def test_no_separators(self) -> None:
        """String with no separators is returned unchanged."""
        assert _normalize_path_separators("filename.py") == "filename.py"


class TestMatchFilePathPattern:
    """Tests for _match_file_path_pattern."""

    # --- Empty / degenerate inputs ---

    def test_empty_file_path_returns_false(self) -> None:
        """Empty file path never matches."""
        assert not _match_file_path_pattern("", "tests/")

    def test_empty_pattern_returns_false(self) -> None:
        """Empty pattern never matches."""
        assert not _match_file_path_pattern("tests/test_module.py", "")

    def test_both_empty_returns_false(self) -> None:
        """Both empty inputs return False."""
        assert not _match_file_path_pattern("", "")

    # --- Directory patterns (contain /) ---

    def test_directory_pattern_single_segment(self) -> None:
        """Single-segment directory pattern matches any segment equal to it."""
        assert _match_file_path_pattern("tests/test_utils.py", "tests/")
        assert _match_file_path_pattern("src/tests/module.py", "tests/")

    def test_directory_pattern_does_not_match_substring(self) -> None:
        """Directory pattern 'tests/' must match whole segment, not 'contest'."""
        assert not _match_file_path_pattern("src/contest/module.py", "tests/")

    def test_directory_pattern_multi_segment(self) -> None:
        """.github/workflows/ pattern matches a multi-segment prefix."""
        assert _match_file_path_pattern(".github/workflows/ci.yaml", ".github/workflows/")

    def test_directory_pattern_multi_segment_not_match_partial(self) -> None:
        """Multi-segment directory pattern does not partially match."""
        assert not _match_file_path_pattern(".github/ci.yaml", ".github/workflows/")

    def test_directory_pattern_non_trailing_slash(self) -> None:
        """Non-trailing slash patterns match subsequences of path segments."""
        assert _match_file_path_pattern(".github/workflows/push.yaml", ".github/workflows")

    # --- Plain word patterns (alphanumeric, word boundary) ---

    def test_plain_word_matches_full_segment(self) -> None:
        """'requirements' matches a segment named 'requirements'."""
        assert _match_file_path_pattern("requirements.txt", "requirements")

    def test_plain_word_matches_in_middle_segment(self) -> None:
        """Plain word matches when it appears as any path segment."""
        assert _match_file_path_pattern("deps/requirements/base.txt", "requirements")

    def test_plain_word_no_false_positive_substring(self) -> None:
        """'test' word boundary must not match 'contest' segment."""
        assert not _match_file_path_pattern("src/contest/file.py", "test")

    def test_plain_word_case_insensitive(self) -> None:
        """Plain word matching is case insensitive."""
        assert _match_file_path_pattern("Makefile", "makefile")
        assert _match_file_path_pattern("makefile", "Makefile")

    # --- Suffix pattern (starts with _) ---

    def test_suffix_pattern_matches(self) -> None:
        """Pattern starting with '_' matches segments ending with that suffix."""
        assert _match_file_path_pattern("module_test.py", "_test.py")

    def test_suffix_pattern_no_false_positive(self) -> None:
        """Suffix pattern doesn't match when suffix is absent."""
        assert not _match_file_path_pattern("test_module.py", "_test.py")

    # --- Prefix pattern (ends with _) ---

    def test_prefix_pattern_matches(self) -> None:
        """Pattern ending with '_' matches segments starting with that prefix."""
        assert _match_file_path_pattern("tests/test_module.py", "test_")

    def test_prefix_pattern_no_false_positive(self) -> None:
        """Prefix pattern doesn't match when prefix is absent."""
        assert not _match_file_path_pattern("tests/module_test.py", "test_")

    # --- Extension / substring patterns ---

    def test_extension_pattern(self) -> None:
        """.pyc extension pattern matches any segment containing '.pyc'."""
        assert _match_file_path_pattern("module.pyc", ".pyc")
        assert _match_file_path_pattern("__pycache__/module.cpython-311.pyc", ".pyc")

    def test_substring_not_present(self) -> None:
        """Substring pattern returns False when not present."""
        assert not _match_file_path_pattern("module.py", ".pyc")

    # --- Windows-style paths ---

    def test_windows_path_separators(self) -> None:
        """Windows backslash separators are normalised before matching."""
        assert _match_file_path_pattern("tests\\test_utils.py", "tests/")
        assert _match_file_path_pattern("tests\\test_utils.py", "test_")


class TestClassifyFileCategory:
    """Tests for classify_file_category."""

    # --- Dependency ---

    def test_uv_lock_is_dependency(self) -> None:
        assert classify_file_category("uv.lock") == FileCategory.DEPENDENCY

    def test_requirements_txt_is_dependency(self) -> None:
        assert classify_file_category("requirements.txt") == FileCategory.DEPENDENCY

    def test_requirements_dev_txt_is_dependency(self) -> None:
        assert classify_file_category("requirements-dev.txt") == FileCategory.DEPENDENCY

    def test_package_lock_json_is_dependency(self) -> None:
        assert classify_file_category("package-lock.json") == FileCategory.DEPENDENCY

    def test_yarn_lock_is_dependency(self) -> None:
        assert classify_file_category("yarn.lock") == FileCategory.DEPENDENCY

    def test_pipfile_lock_is_dependency(self) -> None:
        assert classify_file_category("Pipfile.lock") == FileCategory.DEPENDENCY

    def test_go_sum_is_dependency(self) -> None:
        assert classify_file_category("go.sum") == FileCategory.DEPENDENCY

    def test_cargo_lock_is_dependency(self) -> None:
        assert classify_file_category("Cargo.lock") == FileCategory.DEPENDENCY

    # --- Generated ---

    def test_pycache_is_generated(self) -> None:
        assert classify_file_category("__pycache__/module.cpython-311.pyc") == FileCategory.GENERATED

    def test_pyc_extension_is_generated(self) -> None:
        assert classify_file_category("module.pyc") == FileCategory.GENERATED

    def test_egg_info_dir_is_generated(self) -> None:
        assert classify_file_category("my_pkg.egg-info/RECORD") == FileCategory.GENERATED

    def test_node_modules_is_generated(self) -> None:
        assert classify_file_category("node_modules/lodash/index.js") == FileCategory.GENERATED

    def test_htmlcov_is_generated(self) -> None:
        assert classify_file_category("htmlcov/index.html") == FileCategory.GENERATED

    # --- Style (must be checked before CONFIG) ---

    def test_flake8_is_style_not_config(self) -> None:
        """STYLE takes priority over CONFIG for linting config files."""
        assert classify_file_category(".flake8") == FileCategory.STYLE

    def test_ruff_toml_is_style(self) -> None:
        assert classify_file_category("ruff.toml") == FileCategory.STYLE

    def test_pylintrc_is_style(self) -> None:
        assert classify_file_category(".pylintrc") == FileCategory.STYLE

    def test_prettierrc_is_style(self) -> None:
        assert classify_file_category(".prettierrc") == FileCategory.STYLE

    def test_eslintrc_is_style(self) -> None:
        assert classify_file_category(".eslintrc") == FileCategory.STYLE

    # --- CI ---

    def test_github_workflows_is_ci(self) -> None:
        assert classify_file_category(".github/workflows/ci.yaml") == FileCategory.CI

    def test_gitlab_ci_yml_is_ci(self) -> None:
        assert classify_file_category(".gitlab-ci.yml") == FileCategory.CI

    def test_jenkinsfile_is_ci(self) -> None:
        assert classify_file_category("Jenkinsfile") == FileCategory.CI

    def test_travis_yml_is_ci(self) -> None:
        assert classify_file_category(".travis.yml") == FileCategory.CI

    def test_circleci_config_is_ci(self) -> None:
        assert classify_file_category(".circleci/config.yml") == FileCategory.CI

    def test_azure_pipelines_is_ci(self) -> None:
        assert classify_file_category("azure-pipelines.yml") == FileCategory.CI

    # --- Test ---

    def test_tests_dir_is_test(self) -> None:
        assert classify_file_category("tests/test_utils.py") == FileCategory.TEST

    def test_test_prefix_file_is_test(self) -> None:
        assert classify_file_category("test_module.py") == FileCategory.TEST

    def test_conftest_is_test(self) -> None:
        assert classify_file_category("conftest.py") == FileCategory.TEST

    def test_test_suffix_is_test(self) -> None:
        assert classify_file_category("module_test.py") == FileCategory.TEST

    def test_nested_test_dir_is_test(self) -> None:
        assert classify_file_category("src/tests/test_core.py") == FileCategory.TEST

    # --- Docs ---

    def test_docs_dir_is_docs(self) -> None:
        assert classify_file_category("docs/api.md") == FileCategory.DOCS

    def test_readme_md_is_docs(self) -> None:
        assert classify_file_category("README.md") == FileCategory.DOCS

    def test_changelog_is_docs(self) -> None:
        assert classify_file_category("CHANGELOG.md") == FileCategory.DOCS

    def test_license_is_docs(self) -> None:
        assert classify_file_category("LICENSE") == FileCategory.DOCS

    def test_md_extension_is_docs(self) -> None:
        assert classify_file_category("CONTRIBUTING.md") == FileCategory.DOCS

    # --- Build ---

    def test_dockerfile_is_build(self) -> None:
        assert classify_file_category("Dockerfile") == FileCategory.BUILD

    def test_docker_compose_is_build(self) -> None:
        assert classify_file_category("docker-compose.yml") == FileCategory.BUILD

    def test_makefile_is_build(self) -> None:
        assert classify_file_category("Makefile") == FileCategory.BUILD

    def test_tox_ini_is_build(self) -> None:
        assert classify_file_category("tox.ini") == FileCategory.BUILD

    def test_noxfile_is_build(self) -> None:
        assert classify_file_category("noxfile.py") == FileCategory.BUILD

    def test_dockerignore_is_build(self) -> None:
        assert classify_file_category(".dockerignore") == FileCategory.BUILD

    # --- Config ---

    def test_pyproject_toml_is_config(self) -> None:
        assert classify_file_category("pyproject.toml") == FileCategory.CONFIG

    def test_gitignore_is_config(self) -> None:
        assert classify_file_category(".gitignore") == FileCategory.CONFIG

    def test_setup_py_is_config(self) -> None:
        assert classify_file_category("setup.py") == FileCategory.CONFIG

    def test_setup_cfg_is_config(self) -> None:
        assert classify_file_category("setup.cfg") == FileCategory.CONFIG

    def test_editorconfig_is_config(self) -> None:
        assert classify_file_category(".editorconfig") == FileCategory.CONFIG

    def test_tsconfig_is_config(self) -> None:
        assert classify_file_category("tsconfig.json") == FileCategory.CONFIG

    # --- Production (default fallback) ---

    def test_source_py_is_production(self) -> None:
        assert classify_file_category("git_acp/cli/cli.py") == FileCategory.PRODUCTION

    def test_src_module_is_production(self) -> None:
        assert classify_file_category("src/auth.py") == FileCategory.PRODUCTION

    def test_root_py_file_is_production(self) -> None:
        assert classify_file_category("main.py") == FileCategory.PRODUCTION

    def test_typescript_source_is_production(self) -> None:
        assert classify_file_category("src/components/Button.tsx") == FileCategory.PRODUCTION

    def test_rust_source_is_production(self) -> None:
        assert classify_file_category("src/main.rs") == FileCategory.PRODUCTION

    # --- Priority ordering ---

    def test_style_takes_priority_over_config(self) -> None:
        """STYLE patterns are checked before CONFIG, so .flake8 is STYLE not CONFIG."""
        # .flake8 appears in both STYLE and CONFIG patterns
        result = classify_file_category(".flake8")
        assert result == FileCategory.STYLE
        assert result != FileCategory.CONFIG

    def test_dependency_takes_priority_over_config(self) -> None:
        """DEPENDENCY is checked before CONFIG, so requirements files are DEPENDENCY."""
        result = classify_file_category("requirements.txt")
        assert result == FileCategory.DEPENDENCY

    def test_generated_takes_priority_over_test(self) -> None:
        """GENERATED is checked before TEST, so .pyc files in test dirs are GENERATED."""
        result = classify_file_category("tests/__pycache__/test_mod.cpython-311.pyc")
        assert result == FileCategory.GENERATED


class TestCategorizeChangedFiles:
    """Tests for categorize_changed_files."""

    def test_empty_set_returns_empty_dict(self) -> None:
        """Empty input produces empty output."""
        assert categorize_changed_files(set()) == {}

    def test_single_production_file(self) -> None:
        """Single source file maps to PRODUCTION category."""
        result = categorize_changed_files({"src/module.py"})
        assert result == {FileCategory.PRODUCTION: {"src/module.py"}}

    def test_single_test_file(self) -> None:
        """Single test file maps to TEST category."""
        result = categorize_changed_files({"tests/test_module.py"})
        assert result == {FileCategory.TEST: {"tests/test_module.py"}}

    def test_multiple_files_same_category(self) -> None:
        """Multiple files of the same category are grouped together."""
        files = {"tests/test_a.py", "tests/test_b.py"}
        result = categorize_changed_files(files)
        assert FileCategory.TEST in result
        assert result[FileCategory.TEST] == files

    def test_mixed_categories_all_present(self) -> None:
        """Mixed files produce all expected categories."""
        files = {
            "src/main.py",
            "tests/test_main.py",
            "docs/README.md",
            "uv.lock",
        }
        result = categorize_changed_files(files)
        assert FileCategory.PRODUCTION in result
        assert FileCategory.TEST in result
        assert FileCategory.DOCS in result
        assert FileCategory.DEPENDENCY in result

    def test_mixed_categories_file_membership(self) -> None:
        """Each file appears in exactly the right category."""
        files = {"src/auth.py", "tests/test_auth.py", ".github/workflows/ci.yaml"}
        result = categorize_changed_files(files)
        assert "src/auth.py" in result[FileCategory.PRODUCTION]
        assert "tests/test_auth.py" in result[FileCategory.TEST]
        assert ".github/workflows/ci.yaml" in result[FileCategory.CI]

    def test_only_categories_with_matches_are_included(self) -> None:
        """Categories with no files are excluded from the result."""
        result = categorize_changed_files({"README.md"})
        assert FileCategory.DOCS in result
        assert FileCategory.TEST not in result
        assert FileCategory.PRODUCTION not in result

    def test_returns_dict_of_sets(self) -> None:
        """Result values are sets of file paths."""
        result = categorize_changed_files({"src/module.py"})
        for value in result.values():
            assert isinstance(value, set)

    def test_files_not_duplicated(self) -> None:
        """Each file appears in exactly one category."""
        files = {"src/a.py", "tests/test_a.py", "docs/guide.md"}
        result = categorize_changed_files(files)
        all_files: set[str] = set()
        for category_files in result.values():
            # No file should appear in two categories
            overlap = all_files & category_files
            assert not overlap, f"Files appear in multiple categories: {overlap}"
            all_files.update(category_files)
        assert all_files == files

    def test_large_file_set(self) -> None:
        """Handles a larger set of files without error."""
        files = {
            "git_acp/cli/cli.py",
            "git_acp/git/classification.py",
            "git_acp/config/constants.py",
            "tests/git/test_classification.py",
            "tests/config/test_constants.py",
            "docs/guide.md",
            "README.md",
            ".github/workflows/test.yaml",
            "pyproject.toml",
            "uv.lock",
            "Dockerfile",
            ".flake8",
        }
        result = categorize_changed_files(files)
        # Just verify it runs and produces sensible output
        assert isinstance(result, dict)
        total_categorized = sum(len(v) for v in result.values())
        assert total_categorized == len(files)
