"""
Comprehensive security tests for TargetContext and security utilities.

These tests verify that CodeCompanion cannot be tricked into operating
outside its designated target directory.
"""
import os
import tempfile
import pytest
from pathlib import Path

from codecompanion.target import TargetContext, TargetSecurityError
from codecompanion.security import (
    is_system_directory,
    is_safe_directory,
    validate_no_path_traversal,
    sanitize_filename,
    sanitize_command_arg,
    is_safe_git_branch_name,
    validate_api_key_format,
)


class TestTargetContext:
    """Test suite for TargetContext security features."""

    def test_accepts_valid_directory(self, tmp_path):
        """TargetContext should accept a valid directory."""
        target = TargetContext(tmp_path)
        assert target.root == tmp_path

    def test_rejects_nonexistent_directory(self):
        """TargetContext should reject non-existent directories."""
        with pytest.raises(TargetSecurityError, match="does not exist"):
            TargetContext("/nonexistent/path/12345")

    def test_rejects_system_root(self):
        """TargetContext should reject system root directory."""
        with pytest.raises(TargetSecurityError, match="system directory"):
            TargetContext("/")

    def test_rejects_usr_directory(self):
        """TargetContext should reject /usr directory."""
        with pytest.raises(TargetSecurityError, match="system directory"):
            TargetContext("/usr")

    def test_rejects_etc_directory(self):
        """TargetContext should reject /etc directory."""
        with pytest.raises(TargetSecurityError, match="system directory"):
            TargetContext("/etc")

    def test_rejects_home_directory_itself(self):
        """TargetContext should reject the user's home directory itself."""
        home = Path.home()
        # Home directory might be caught as system directory (like /root) or explicitly as home
        with pytest.raises(TargetSecurityError, match="(home directory|system directory)"):
            TargetContext(home)

    def test_safe_path_accepts_simple_relative(self, tmp_path):
        """safe_path should accept simple relative paths."""
        target = TargetContext(tmp_path)
        result = target.safe_path("subdir/file.txt")
        assert result == tmp_path / "subdir/file.txt"

    def test_safe_path_rejects_parent_traversal(self, tmp_path):
        """safe_path should reject ../ path traversal."""
        target = TargetContext(tmp_path)
        with pytest.raises(TargetSecurityError, match="escapes target"):
            target.safe_path("../../etc/passwd")

    def test_safe_path_rejects_absolute_outside(self, tmp_path):
        """safe_path should reject absolute paths outside target."""
        target = TargetContext(tmp_path)
        with pytest.raises(TargetSecurityError, match="escapes target"):
            target.safe_path("/etc/passwd")

    def test_safe_path_accepts_absolute_inside(self, tmp_path):
        """safe_path should accept absolute paths that are inside target."""
        target = TargetContext(tmp_path)
        inside_path = tmp_path / "valid" / "file.txt"
        result = target.safe_path(str(inside_path))
        assert result == inside_path

    def test_safe_path_resolves_symlinks(self, tmp_path):
        """safe_path should resolve symlinks and validate the target."""
        # Create a symlink pointing outside
        outside = Path("/tmp")
        link_path = tmp_path / "evil_link"

        try:
            link_path.symlink_to(outside)
            target = TargetContext(tmp_path)

            # This should fail because the symlink points outside
            with pytest.raises(TargetSecurityError):
                target.safe_path("evil_link")
        except OSError:
            # Symlink creation might fail in some environments
            pytest.skip("Cannot create symlinks in this environment")

    def test_safe_cmd_executes_in_target(self, tmp_path):
        """safe_cmd should execute commands in the target directory."""
        target = TargetContext(tmp_path)
        result = target.safe_cmd("pwd")
        assert result['code'] == 0
        assert str(tmp_path) in result['stdout']

    def test_safe_cmd_returns_correct_structure(self, tmp_path):
        """safe_cmd should return dict with code, stdout, stderr."""
        target = TargetContext(tmp_path)
        result = target.safe_cmd("echo test")
        assert 'code' in result
        assert 'stdout' in result
        assert 'stderr' in result
        assert result['code'] == 0
        assert 'test' in result['stdout']

    def test_read_file_works_for_valid_path(self, tmp_path):
        """read_file should read files within target."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        target = TargetContext(tmp_path)
        content = target.read_file("test.txt")
        assert content == "Hello, World!"

    def test_read_file_rejects_path_traversal(self, tmp_path):
        """read_file should reject path traversal attempts."""
        target = TargetContext(tmp_path)
        with pytest.raises(TargetSecurityError):
            target.read_file("../../etc/passwd")

    def test_write_file_creates_in_target(self, tmp_path):
        """write_file should create files within target."""
        target = TargetContext(tmp_path)
        target.write_file("output.txt", "test content")

        result_file = tmp_path / "output.txt"
        assert result_file.exists()
        assert result_file.read_text() == "test content"

    def test_write_file_rejects_path_traversal(self, tmp_path):
        """write_file should reject path traversal attempts."""
        target = TargetContext(tmp_path)
        with pytest.raises(TargetSecurityError):
            target.write_file("../../../tmp/evil.txt", "malicious")

    def test_write_file_creates_parent_dirs(self, tmp_path):
        """write_file should create parent directories as needed."""
        target = TargetContext(tmp_path)
        target.write_file("deep/nested/file.txt", "content")

        result_file = tmp_path / "deep/nested/file.txt"
        assert result_file.exists()
        assert result_file.read_text() == "content"

    def test_file_exists_returns_true_for_existing(self, tmp_path):
        """file_exists should return True for existing files."""
        test_file = tmp_path / "exists.txt"
        test_file.write_text("I exist")

        target = TargetContext(tmp_path)
        assert target.file_exists("exists.txt") is True

    def test_file_exists_returns_false_for_missing(self, tmp_path):
        """file_exists should return False for missing files."""
        target = TargetContext(tmp_path)
        assert target.file_exists("missing.txt") is False

    def test_file_exists_returns_false_for_traversal(self, tmp_path):
        """file_exists should return False for path traversal attempts."""
        target = TargetContext(tmp_path)
        assert target.file_exists("../../etc/passwd") is False

    def test_mkdir_creates_directory(self, tmp_path):
        """mkdir should create directories within target."""
        target = TargetContext(tmp_path)
        new_dir = target.mkdir("newdir")

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert new_dir == tmp_path / "newdir"

    def test_mkdir_rejects_path_traversal(self, tmp_path):
        """mkdir should reject path traversal attempts."""
        target = TargetContext(tmp_path)
        with pytest.raises(TargetSecurityError):
            target.mkdir("../../../tmp/evil")

    def test_cc_dir_property(self, tmp_path):
        """cc_dir should return .cc directory within target."""
        target = TargetContext(tmp_path)
        assert target.cc_dir == tmp_path / ".cc"

    def test_workspace_file_property(self, tmp_path):
        """workspace_file should return workspace.json path."""
        target = TargetContext(tmp_path)
        assert target.workspace_file == tmp_path / ".cc/workspace.json"

    def test_agents_dir_property(self, tmp_path):
        """agents_dir should return agents directory path."""
        target = TargetContext(tmp_path)
        assert target.agents_dir == tmp_path / ".cc/agents"


class TestSecurityUtilities:
    """Test suite for security utility functions."""

    def test_is_system_directory_identifies_root(self):
        """is_system_directory should identify / as system directory."""
        assert is_system_directory(Path("/")) is True

    def test_is_system_directory_identifies_etc(self):
        """is_system_directory should identify /etc as system directory."""
        assert is_system_directory(Path("/etc")) is True

    def test_is_system_directory_allows_user_dirs(self, tmp_path):
        """is_system_directory should allow user directories."""
        assert is_system_directory(tmp_path) is False

    def test_is_safe_directory_rejects_nonexistent(self):
        """is_safe_directory should reject non-existent paths."""
        assert is_safe_directory(Path("/nonexistent/12345")) is False

    def test_is_safe_directory_rejects_system_dirs(self):
        """is_safe_directory should reject system directories."""
        assert is_safe_directory(Path("/etc")) is False

    def test_is_safe_directory_accepts_valid_dirs(self, tmp_path):
        """is_safe_directory should accept valid directories."""
        assert is_safe_directory(tmp_path) is True

    def test_validate_no_path_traversal_accepts_child(self, tmp_path):
        """validate_no_path_traversal should accept child paths."""
        child = tmp_path / "subdir/file.txt"
        validate_no_path_traversal(tmp_path, child)  # Should not raise

    def test_validate_no_path_traversal_rejects_parent(self, tmp_path):
        """validate_no_path_traversal should reject parent paths."""
        parent = tmp_path.parent
        with pytest.raises(ValueError, match="Path traversal"):
            validate_no_path_traversal(tmp_path, parent)

    def test_sanitize_filename_removes_slashes(self):
        """sanitize_filename should remove path separators by default."""
        result = sanitize_filename("../../etc/passwd")
        assert "/" not in result
        assert "\\" not in result

    def test_sanitize_filename_removes_null_bytes(self):
        """sanitize_filename should remove null bytes."""
        result = sanitize_filename("file\x00name.txt")
        assert "\x00" not in result

    def test_sanitize_filename_limits_length(self):
        """sanitize_filename should limit filename length."""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_sanitize_command_arg_quotes_dangerous_chars(self):
        """sanitize_command_arg should quote dangerous characters."""
        result = sanitize_command_arg("file; rm -rf /")
        # Should be properly quoted
        assert ";" not in result or "'" in result or '"' in result

    def test_is_safe_git_branch_name_accepts_valid(self):
        """is_safe_git_branch_name should accept valid branch names."""
        assert is_safe_git_branch_name("feature/my-feature") is True
        assert is_safe_git_branch_name("bugfix/issue-123") is True
        assert is_safe_git_branch_name("main") is True

    def test_is_safe_git_branch_name_rejects_traversal(self):
        """is_safe_git_branch_name should reject path traversal."""
        assert is_safe_git_branch_name("../etc/passwd") is False

    def test_is_safe_git_branch_name_rejects_special_chars(self):
        """is_safe_git_branch_name should reject shell metacharacters."""
        assert is_safe_git_branch_name("branch; rm -rf /") is False
        assert is_safe_git_branch_name("branch`whoami`") is False

    def test_is_safe_git_branch_name_rejects_spaces(self):
        """is_safe_git_branch_name should reject spaces."""
        assert is_safe_git_branch_name("my branch") is False

    def test_validate_api_key_format_anthropic(self):
        """validate_api_key_format should validate Anthropic key format."""
        assert validate_api_key_format("sk-ant-api03-xxxxxxxxxxxx", "anthropic") is True
        assert validate_api_key_format("invalid-key", "anthropic") is False

    def test_validate_api_key_format_openai(self):
        """validate_api_key_format should validate OpenAI key format."""
        assert validate_api_key_format("sk-xxxxxxxxxxxx", "openai") is True
        assert validate_api_key_format("invalid-key", "openai") is False

    def test_validate_api_key_format_rejects_short_keys(self):
        """validate_api_key_format should reject very short keys."""
        assert validate_api_key_format("short", "anthropic") is False


@pytest.fixture
def safe_test_repo():
    """Fixture providing path to safe test repository."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    return fixtures_dir / "safe_repo"


@pytest.fixture
def malicious_test_repo():
    """Fixture providing path to malicious test repository."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    return fixtures_dir / "malicious_repo"


class TestRealWorldScenarios:
    """Integration tests using fixture repositories."""

    def test_can_operate_on_safe_repo(self, safe_test_repo):
        """Should successfully operate on a safe repository."""
        target = TargetContext(safe_test_repo)
        assert target.file_exists("main.py")
        assert target.file_exists("README.md")

    def test_can_read_files_in_safe_repo(self, safe_test_repo):
        """Should successfully read files in safe repository."""
        target = TargetContext(safe_test_repo)
        content = target.read_file("main.py")
        assert "def hello_world" in content

    def test_can_execute_commands_in_safe_repo(self, safe_test_repo):
        """Should successfully execute commands in safe repository."""
        target = TargetContext(safe_test_repo)
        result = target.safe_cmd("ls -la")
        assert result['code'] == 0
        assert "main.py" in result['stdout']
