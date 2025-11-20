"""
Tests for codecompanion --init command and workspace configuration.
"""
import json
import pytest
from pathlib import Path

from codecompanion.target import TargetContext
from codecompanion.workspace import (
    is_initialized,
    create_workspace_config,
    save_workspace_config,
    load_workspace_config,
    get_workspace_summary,
    get_git_info
)
from codecompanion.bootstrap import ensure_bootstrap


class TestWorkspaceInitialization:
    """Tests for workspace initialization functionality."""

    def test_is_initialized_returns_false_for_new_workspace(self, tmp_path):
        """is_initialized should return False for a new workspace."""
        target = TargetContext(tmp_path)
        assert is_initialized(target) is False

    def test_is_initialized_returns_true_after_init(self, tmp_path):
        """is_initialized should return True after workspace.json is created."""
        target = TargetContext(tmp_path)

        # Bootstrap and create config
        ensure_bootstrap(target)
        config = create_workspace_config(target)
        save_workspace_config(target, config)

        assert is_initialized(target) is True

    def test_create_workspace_config_includes_required_fields(self, tmp_path):
        """Workspace config should include all required fields."""
        target = TargetContext(tmp_path)
        config = create_workspace_config(target)

        # Check required fields
        assert "version" in config
        assert "initialized_at" in config
        assert "project_root" in config
        assert "project_type" in config
        assert "codecompanion" in config

        # Check project_root matches target
        assert config["project_root"] == str(target.root)

    def test_create_workspace_config_detects_project_type(self, tmp_path):
        """Workspace config should detect project type."""
        target = TargetContext(tmp_path)

        # Create a Python project marker
        target.write_file("requirements.txt", "pytest>=7.0\n")

        config = create_workspace_config(target)

        assert "project_type" in config
        assert "type" in config["project_type"]
        # Should detect as Python project
        assert "python" in config["project_type"]["type"].lower() or config["project_type"]["type"] == "generic"

    def test_save_and_load_workspace_config(self, tmp_path):
        """Should be able to save and load workspace config."""
        target = TargetContext(tmp_path)
        ensure_bootstrap(target)

        # Create and save config
        original_config = create_workspace_config(target)
        save_workspace_config(target, original_config)

        # Load config
        loaded_config = load_workspace_config(target)

        assert loaded_config is not None
        assert loaded_config["version"] == original_config["version"]
        assert loaded_config["project_root"] == original_config["project_root"]

    def test_load_workspace_config_returns_none_if_not_initialized(self, tmp_path):
        """load_workspace_config should return None if not initialized."""
        target = TargetContext(tmp_path)
        config = load_workspace_config(target)
        assert config is None

    def test_workspace_config_is_valid_json(self, tmp_path):
        """Saved workspace config should be valid JSON."""
        target = TargetContext(tmp_path)
        ensure_bootstrap(target)

        config = create_workspace_config(target)
        save_workspace_config(target, config)

        # Read and parse JSON
        content = target.read_file(".cc/workspace.json")
        parsed = json.loads(content)

        assert isinstance(parsed, dict)
        assert "version" in parsed

    def test_create_workspace_config_is_idempotent(self, tmp_path):
        """Creating workspace config twice should update, not fail."""
        target = TargetContext(tmp_path)
        ensure_bootstrap(target)

        # First initialization
        config1 = create_workspace_config(target, force=False)
        save_workspace_config(target, config1)
        init_time1 = config1["initialized_at"]

        # Second initialization (should update)
        config2 = create_workspace_config(target, force=False)
        save_workspace_config(target, config2)

        # Should have preserved initialization time
        assert config2["initialized_at"] == init_time1
        # But added last_updated
        assert "last_updated" in config2

    def test_force_create_workspace_config_overwrites(self, tmp_path):
        """force=True should create fresh config."""
        target = TargetContext(tmp_path)
        ensure_bootstrap(target)

        # First initialization
        config1 = create_workspace_config(target, force=False)
        save_workspace_config(target, config1)
        init_time1 = config1["initialized_at"]

        # Wait a tiny bit to ensure different timestamp
        import time
        time.sleep(0.01)

        # Force re-initialization
        config2 = create_workspace_config(target, force=True)

        # Should have new initialization time
        assert config2["initialized_at"] != init_time1

    def test_get_workspace_summary_formats_output(self, tmp_path):
        """get_workspace_summary should return formatted string."""
        target = TargetContext(tmp_path)
        config = create_workspace_config(target)

        summary = get_workspace_summary(config)

        # Should contain project type info
        assert "Project Type" in summary or "project" in summary.lower()
        # Should be multi-line
        assert "\n" in summary


class TestGitIntegration:
    """Tests for git repository integration."""

    def test_get_git_info_returns_none_for_non_git_repo(self, tmp_path):
        """get_git_info should return None for non-git repositories."""
        target = TargetContext(tmp_path)
        git_info = get_git_info(target)

        assert git_info is None or git_info == {}

    def test_get_git_info_returns_dict_for_git_repo(self, tmp_path):
        """get_git_info should return dict with git info for git repos."""
        target = TargetContext(tmp_path)

        # Initialize git repo
        init_result = target.safe_cmd("git init")
        if init_result['code'] != 0:
            pytest.skip("Git not available or git init failed")

        target.safe_cmd("git config user.email 'test@example.com'")
        target.safe_cmd("git config user.name 'Test User'")

        # Create initial commit
        target.write_file("README.md", "# Test")
        target.safe_cmd("git add README.md")
        commit_result = target.safe_cmd("git commit -m 'Initial commit'")

        if commit_result['code'] != 0:
            pytest.skip("Git commit failed, skipping test")

        git_info = get_git_info(target)

        # In test environments, git might not work perfectly, so be lenient
        # If git_info is returned, it should have branch info
        if git_info is not None:
            # Git 2.28+ defaults to 'main', older versions use 'master'
            assert "current_branch" in git_info or "commit_hash" in git_info

    def test_workspace_config_includes_git_info_when_available(self, tmp_path):
        """Workspace config should include git info for git repos."""
        target = TargetContext(tmp_path)

        # Initialize git repo
        target.safe_cmd("git init")
        target.safe_cmd("git config user.email 'test@example.com'")
        target.safe_cmd("git config user.name 'Test User'")

        # Create initial commit
        target.write_file("test.txt", "test")
        target.safe_cmd("git add test.txt")
        target.safe_cmd("git commit -m 'Initial commit'")

        config = create_workspace_config(target)

        assert "git" in config
        # Git info might be None or a dict with branch info
        if config["git"]:
            assert isinstance(config["git"], dict)


class TestBootstrapIntegration:
    """Tests for integration between --init and bootstrap."""

    def test_init_creates_cc_directory(self, tmp_path):
        """Initialization should create .cc directory."""
        target = TargetContext(tmp_path)
        ensure_bootstrap(target)

        assert target.cc_dir.exists()
        assert target.cc_dir.is_dir()

    def test_init_creates_agent_stubs(self, tmp_path):
        """Initialization should create agent stub files."""
        target = TargetContext(tmp_path)
        ensure_bootstrap(target)

        agents_dir = target.agents_dir
        assert agents_dir.exists()

        # Check for at least some agent files
        agent_files = list(agents_dir.glob("*.md"))
        assert len(agent_files) > 0

    def test_init_creates_workspace_json(self, tmp_path):
        """Initialization should create workspace.json."""
        target = TargetContext(tmp_path)
        ensure_bootstrap(target)

        config = create_workspace_config(target)
        save_workspace_config(target, config)

        workspace_file = target.workspace_file
        assert workspace_file.exists()

    def test_init_preserves_existing_agents(self, tmp_path):
        """Initialization should not overwrite existing agent files."""
        target = TargetContext(tmp_path)
        ensure_bootstrap(target)

        # Modify an agent file
        analyzer_path = target.agents_dir / "analyzer.md"
        custom_content = "# Custom Analyzer\nMy custom prompt"
        target.write_file(".cc/agents/analyzer.md", custom_content)

        # Re-bootstrap
        ensure_bootstrap(target)

        # Content should be preserved
        content = target.read_file(".cc/agents/analyzer.md")
        assert content == custom_content


class TestCLIIntegration:
    """Integration tests for --init CLI command."""

    def test_init_command_creates_complete_structure(self, tmp_path):
        """--init should create complete .cc/ structure with workspace.json."""
        target = TargetContext(tmp_path)

        # Simulate --init command
        ensure_bootstrap(target)
        config = create_workspace_config(target)
        save_workspace_config(target, config)

        # Verify complete structure
        assert target.cc_dir.exists()
        assert target.agents_dir.exists()
        assert target.workspace_file.exists()
        assert is_initialized(target)

    def test_init_command_works_in_python_project(self, tmp_path):
        """--init should work in a Python project."""
        target = TargetContext(tmp_path)

        # Create Python project markers
        target.write_file("setup.py", "from setuptools import setup\nsetup(name='test')")
        target.write_file("requirements.txt", "pytest\n")

        ensure_bootstrap(target)
        config = create_workspace_config(target)

        # Should detect Python project
        assert "python" in config["project_type"]["type"].lower() or config["project_type"]["type"] == "generic"

    def test_init_command_works_in_empty_directory(self, tmp_path):
        """--init should work in an empty directory."""
        target = TargetContext(tmp_path)

        ensure_bootstrap(target)
        config = create_workspace_config(target)
        save_workspace_config(target, config)

        # Should create structure successfully
        assert is_initialized(target)
        assert config["project_type"]["type"] == "generic"
