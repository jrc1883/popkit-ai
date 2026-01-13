#!/usr/bin/env python3
"""
Test suite for detect_project_type.py

Tests project type detection for project initialization.
Critical for setting up new projects correctly.
"""

import json
import sys
from pathlib import Path

import pytest

# Add popkit-core skills to path
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent.parent
        / "popkit-core"
        / "skills"
        / "pop-project-init"
        / "scripts"
    ),
)

from detect_project_type import detect_existing_project, get_template_info, suggest_project_type


class TestDetectExistingProject:
    """Test existing project detection"""

    def test_empty_directory(self, temp_dir):
        """Test detection in empty directory"""
        result = detect_existing_project(temp_dir)

        assert result["has_existing_project"] is False
        assert result["indicators"]["has_git"] is False
        assert result["indicators"]["has_package_json"] is False
        assert len(result["frameworks"]) == 0
        assert result["category"] is None

    def test_git_only(self, temp_dir):
        """Test detection with only .git directory"""
        (temp_dir / ".git").mkdir()
        result = detect_existing_project(temp_dir)

        assert result["indicators"]["has_git"] is True
        assert result["has_existing_project"] is False  # Git alone doesn't make it a project

    def test_node_project_basic(self, temp_dir):
        """Test detection of basic Node.js project"""
        package_json = temp_dir / "package.json"
        package_json.write_text(json.dumps({"name": "test-project", "version": "1.0.0"}))

        result = detect_existing_project(temp_dir)

        assert result["has_existing_project"] is True
        assert result["indicators"]["has_package_json"] is True
        assert len(result["frameworks"]) == 0  # No specific framework

    def test_nextjs_project(self, temp_dir):
        """Test detection of Next.js project"""
        package_json = temp_dir / "package.json"
        package_json.write_text(
            json.dumps(
                {"name": "test-nextjs", "dependencies": {"next": "^14.0.0", "react": "^18.0.0"}}
            )
        )

        result = detect_existing_project(temp_dir)

        assert result["has_existing_project"] is True
        assert "nextjs" in result["frameworks"]
        assert result["category"] == "web-frontend"

    def test_react_without_nextjs(self, temp_dir):
        """Test detection of React project without Next.js"""
        package_json = temp_dir / "package.json"
        package_json.write_text(
            json.dumps(
                {"name": "test-react", "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}}
            )
        )

        result = detect_existing_project(temp_dir)

        assert "react" in result["frameworks"]
        assert "nextjs" not in result["frameworks"]
        assert result["category"] == "web-frontend"

    def test_express_backend(self, temp_dir):
        """Test detection of Express.js backend"""
        package_json = temp_dir / "package.json"
        package_json.write_text(
            json.dumps({"name": "test-express", "dependencies": {"express": "^4.18.0"}})
        )

        result = detect_existing_project(temp_dir)

        assert "express" in result["frameworks"]
        assert result["category"] == "web-backend"

    def test_typescript_project(self, temp_dir):
        """Test detection of TypeScript project"""
        package_json = temp_dir / "package.json"
        package_json.write_text(
            json.dumps({"name": "test-ts", "devDependencies": {"typescript": "^5.0.0"}})
        )

        result = detect_existing_project(temp_dir)

        assert "typescript" in result["frameworks"]
        assert result["category"] == "cli-or-library"

    def test_python_fastapi_project(self, temp_dir):
        """Test detection of FastAPI project"""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text("""
[tool.poetry]
name = "test-fastapi"

[tool.poetry.dependencies]
python = "^3.9"
fastapi = "^0.104.0"
        """)

        result = detect_existing_project(temp_dir)

        assert result["has_existing_project"] is True
        assert result["indicators"]["has_pyproject"] is True
        assert "fastapi" in result["frameworks"]
        assert result["category"] == "web-backend"

    def test_python_django_project(self, temp_dir):
        """Test detection of Django project"""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text("""
[tool.poetry.dependencies]
django = "^4.2.0"
        """)

        result = detect_existing_project(temp_dir)

        assert "django" in result["frameworks"]
        assert result["category"] == "web-backend"

    def test_python_click_cli(self, temp_dir):
        """Test detection of Click CLI project"""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text("""
[tool.poetry.dependencies]
click = "^8.0.0"
        """)

        result = detect_existing_project(temp_dir)

        assert "cli-python" in result["frameworks"]
        assert result["category"] == "cli-or-library"

    def test_rust_project(self, temp_dir):
        """Test detection of Rust project"""
        cargo = temp_dir / "Cargo.toml"
        cargo.write_text("""
[package]
name = "test-rust"
version = "0.1.0"
        """)

        result = detect_existing_project(temp_dir)

        assert result["has_existing_project"] is True
        assert result["indicators"]["has_cargo"] is True

    def test_go_project(self, temp_dir):
        """Test detection of Go project"""
        go_mod = temp_dir / "go.mod"
        go_mod.write_text("""
module example.com/test

go 1.21
        """)

        result = detect_existing_project(temp_dir)

        assert result["has_existing_project"] is True
        assert result["indicators"]["has_go_mod"] is True

    def test_malformed_package_json(self, temp_dir):
        """Test handling of malformed package.json"""
        package_json = temp_dir / "package.json"
        package_json.write_text("{ invalid json }")

        result = detect_existing_project(temp_dir)

        # Should not crash, just skip framework detection
        assert result["indicators"]["has_package_json"] is True
        assert len(result["frameworks"]) == 0

    def test_malformed_pyproject_toml(self, temp_dir):
        """Test handling of malformed pyproject.toml"""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text("[ invalid toml")

        result = detect_existing_project(temp_dir)

        # Should not crash
        assert result["indicators"]["has_pyproject"] is True
        assert len(result["frameworks"]) == 0

    def test_multiple_frameworks(self, temp_dir):
        """Test detection with multiple frameworks"""
        package_json = temp_dir / "package.json"
        package_json.write_text(
            json.dumps(
                {"dependencies": {"next": "^14.0.0", "express": "^4.18.0", "typescript": "^5.0.0"}}
            )
        )

        result = detect_existing_project(temp_dir)

        assert "nextjs" in result["frameworks"]
        assert "express" in result["frameworks"]
        assert "typescript" in result["frameworks"]
        # Frontend takes precedence
        assert result["category"] == "web-frontend"

    def test_vue_project(self, temp_dir):
        """Test detection of Vue.js project"""
        package_json = temp_dir / "package.json"
        package_json.write_text(json.dumps({"dependencies": {"vue": "^3.3.0"}}))

        result = detect_existing_project(temp_dir)

        assert "vue" in result["frameworks"]
        assert result["category"] == "web-frontend"

    def test_fastify_backend(self, temp_dir):
        """Test detection of Fastify backend"""
        package_json = temp_dir / "package.json"
        package_json.write_text(json.dumps({"dependencies": {"fastify": "^4.24.0"}}))

        result = detect_existing_project(temp_dir)

        assert "fastify" in result["frameworks"]
        assert result["category"] == "web-backend"


class TestSuggestProjectType:
    """Test project type suggestion"""

    def test_suggest_for_nextjs_project(self, temp_dir):
        """Test suggestions for detected Next.js project"""
        package_json = temp_dir / "package.json"
        package_json.write_text(json.dumps({"dependencies": {"next": "^14.0.0"}}))

        detection = detect_existing_project(temp_dir)
        suggestions = suggest_project_type(detection)

        assert len(suggestions["suggestions"]) >= 1
        assert suggestions["suggestions"][0]["type"] == "nextjs"
        assert suggestions["suggestions"][0]["confidence"] == "high"
        assert suggestions["recommended"] is not None
        assert suggestions["recommended"]["type"] == "nextjs"

    def test_suggest_for_fastapi_project(self, temp_dir):
        """Test suggestions for detected FastAPI project"""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text('[tool.poetry.dependencies]\nfastapi = "^0.104.0"')

        detection = detect_existing_project(temp_dir)
        suggestions = suggest_project_type(detection)

        assert suggestions["suggestions"][0]["type"] == "fastapi"
        assert suggestions["suggestions"][0]["confidence"] == "high"

    def test_suggest_for_empty_directory(self, temp_dir):
        """Test suggestions for empty directory"""
        detection = detect_existing_project(temp_dir)
        suggestions = suggest_project_type(detection)

        # Should suggest common options
        assert len(suggestions["suggestions"]) >= 4
        suggestion_types = [s["type"] for s in suggestions["suggestions"]]
        assert "nextjs" in suggestion_types
        assert "fastapi" in suggestion_types
        assert "cli" in suggestion_types
        assert "library" in suggestion_types

    def test_suggestions_have_required_fields(self, temp_dir):
        """Test that all suggestions have required fields"""
        detection = detect_existing_project(temp_dir)
        suggestions = suggest_project_type(detection)

        for suggestion in suggestions["suggestions"]:
            assert "type" in suggestion
            assert "confidence" in suggestion
            assert "reason" in suggestion

    def test_recommended_is_first_suggestion(self, temp_dir):
        """Test that recommended matches first suggestion"""
        detection = detect_existing_project(temp_dir)
        suggestions = suggest_project_type(detection)

        if suggestions["suggestions"]:
            assert suggestions["recommended"] == suggestions["suggestions"][0]


class TestGetTemplateInfo:
    """Test template information retrieval"""

    def test_nextjs_template(self):
        """Test Next.js template info"""
        info = get_template_info("nextjs")

        assert info["name"] == "Next.js Application"
        assert "description" in info
        assert "features" in info
        assert "files_created" in info
        assert isinstance(info["features"], list)
        assert len(info["features"]) > 0
        assert "TypeScript" in info["features"]

    def test_fastapi_template(self):
        """Test FastAPI template info"""
        info = get_template_info("fastapi")

        assert info["name"] == "FastAPI Service"
        assert "description" in info
        assert "features" in info
        assert "optional_features" in info
        assert "Pydantic Settings" in info["features"]

    def test_cli_template(self):
        """Test CLI template info"""
        info = get_template_info("cli")

        assert info["name"] == "CLI Tool"
        assert "Click Framework" in info["features"]

    def test_library_template(self):
        """Test library template info"""
        info = get_template_info("library")

        assert info["name"] == "Library/Package"
        assert "TypeScript Types" in info["features"]

    def test_plugin_template(self):
        """Test Claude Code plugin template info"""
        info = get_template_info("plugin")

        assert info["name"] == "Claude Code Plugin"
        assert "Skill Templates" in info["features"]

    def test_unknown_template(self):
        """Test unknown template type"""
        info = get_template_info("unknown-type")

        assert info == {}

    def test_all_templates_have_files_created(self):
        """Test that all templates list files they create"""
        templates = ["nextjs", "fastapi", "cli", "library", "plugin"]

        for template_type in templates:
            info = get_template_info(template_type)
            assert "files_created" in info
            assert isinstance(info["files_created"], list)
            assert len(info["files_created"]) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory"""
        fake_dir = Path("/nonexistent/path/12345")
        result = detect_existing_project(fake_dir)

        # Should handle gracefully (Path.exists returns False)
        assert isinstance(result, dict)
        assert "has_existing_project" in result

    def test_file_instead_of_directory(self, temp_dir):
        """Test handling when given a file instead of directory"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        result = detect_existing_project(test_file)

        # Should handle gracefully
        assert isinstance(result, dict)

    def test_readonly_package_json(self, temp_dir):
        """Test handling of read-only package.json"""
        package_json = temp_dir / "package.json"
        package_json.write_text('{"name": "test"}')

        # Make read-only (platform-dependent behavior)
        import stat

        package_json.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        try:
            result = detect_existing_project(temp_dir)
            assert result["indicators"]["has_package_json"] is True
        finally:
            # Restore write permissions for cleanup
            package_json.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    def test_empty_package_json(self, temp_dir):
        """Test handling of empty package.json"""
        package_json = temp_dir / "package.json"
        package_json.write_text("{}")

        result = detect_existing_project(temp_dir)

        assert result["has_existing_project"] is True
        assert result["indicators"]["has_package_json"] is True
        assert len(result["frameworks"]) == 0

    def test_package_json_with_null_dependencies(self, temp_dir):
        """Test handling of null dependencies"""
        package_json = temp_dir / "package.json"
        package_json.write_text(json.dumps({"name": "test", "dependencies": None}))

        result = detect_existing_project(temp_dir)

        # Should handle gracefully
        assert result["has_existing_project"] is True

    def test_case_insensitive_framework_detection(self, temp_dir):
        """Test case-insensitive framework name detection"""
        pyproject = temp_dir / "pyproject.toml"
        pyproject.write_text("""
[tool.poetry.dependencies]
FastAPI = "^0.104.0"
Django = "^4.2.0"
        """)

        result = detect_existing_project(temp_dir)

        # Should detect regardless of case
        assert "fastapi" in result["frameworks"] or "django" in result["frameworks"]

    def test_indicators_all_false(self, temp_dir):
        """Test that empty directory has all indicators false"""
        result = detect_existing_project(temp_dir)

        for key, value in result["indicators"].items():
            assert value is False

    def test_setup_py_detection(self, temp_dir):
        """Test detection of legacy setup.py"""
        setup_py = temp_dir / "setup.py"
        setup_py.write_text("""
from setuptools import setup
setup(name='test-project')
        """)

        result = detect_existing_project(temp_dir)

        assert result["indicators"]["has_setup_py"] is True

    def test_readme_detection(self, temp_dir):
        """Test README.md detection"""
        readme = temp_dir / "README.md"
        readme.write_text("# Test Project")

        result = detect_existing_project(temp_dir)

        assert result["indicators"]["has_readme"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
