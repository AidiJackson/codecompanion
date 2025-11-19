"""
Target isolation and security context for CodeCompanion.

This module provides the TargetContext class, which ensures all file operations,
subprocess calls, and git operations stay within a designated target directory.
This is critical for security when CodeCompanion operates on arbitrary repositories.
"""
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Union


class TargetSecurityError(Exception):
    """Raised when a security boundary would be violated."""
    pass


class TargetContext:
    """
    Secure context for operating on a target repository.

    All file operations and subprocess calls must go through this context
    to ensure they stay within the target directory boundaries.

    Example:
        >>> target = TargetContext("/home/user/my-project")
        >>> target.safe_path("src/main.py")  # OK
        >>> target.safe_path("../../etc/passwd")  # Raises TargetSecurityError
    """

    # System directories that should never be used as targets
    FORBIDDEN_PATHS = [
        Path("/"),
        Path("/usr"),
        Path("/etc"),
        Path("/bin"),
        Path("/sbin"),
        Path("/var"),
        Path("/home"),
        Path("/root"),
        Path("/boot"),
        Path("/sys"),
        Path("/proc"),
        Path("/dev"),
    ]

    def __init__(self, target_root: Union[str, Path]):
        """
        Initialize a target context.

        Args:
            target_root: Path to the target repository/directory

        Raises:
            TargetSecurityError: If target_root is unsafe
        """
        self._root = Path(target_root).resolve()
        self._validate_target()

    def _validate_target(self) -> None:
        """Validate that the target directory is safe to operate on."""
        # Check if directory exists
        if not self._root.exists():
            raise TargetSecurityError(
                f"Target directory does not exist: {self._root}"
            )

        if not self._root.is_dir():
            raise TargetSecurityError(
                f"Target path is not a directory: {self._root}"
            )

        # Check against forbidden paths
        for forbidden in self.FORBIDDEN_PATHS:
            try:
                # Check if target is the forbidden path or a subdirectory of it
                if self._root == forbidden:
                    raise TargetSecurityError(
                        f"Refusing to operate on system directory: {self._root}"
                    )
                # Also block if it's directly under a forbidden path (like /home/user is under /home)
                # But allow normal user directories
                if forbidden in [Path("/"), Path("/home"), Path("/root")]:
                    continue
                if self._root.is_relative_to(forbidden):
                    raise TargetSecurityError(
                        f"Target is within forbidden directory {forbidden}: {self._root}"
                    )
            except (ValueError, TypeError):
                # is_relative_to can raise these on some systems
                pass

        # Additional check: Don't allow user's home directory itself
        try:
            home = Path.home()
            if self._root == home:
                raise TargetSecurityError(
                    f"Refusing to operate on home directory itself: {self._root}. "
                    "Please target a specific project subdirectory."
                )
        except (RuntimeError, KeyError):
            # Path.home() can fail in some environments
            pass

    def safe_path(self, rel_path: Union[str, Path]) -> Path:
        """
        Resolve a relative path within the target, ensuring it stays within bounds.

        Args:
            rel_path: Relative path within the target directory

        Returns:
            Absolute resolved path

        Raises:
            TargetSecurityError: If the path would escape the target directory
        """
        # Convert to Path
        candidate = Path(rel_path)

        # If it's already absolute, check if it's within our root
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            # Resolve relative to our root
            resolved = (self._root / candidate).resolve()

        # Ensure the resolved path is within our root
        try:
            resolved.relative_to(self._root)
        except ValueError:
            raise TargetSecurityError(
                f"Path escapes target directory: {rel_path} -> {resolved} "
                f"(target root: {self._root})"
            )

        return resolved

    def safe_cmd(self, cmd: str, **kwargs) -> dict:
        """
        Execute a shell command within the target directory.

        Args:
            cmd: Shell command to execute
            **kwargs: Additional arguments to subprocess.run (except cwd)

        Returns:
            dict with 'code', 'stdout', 'stderr' keys
        """
        # Force cwd to be our target root
        kwargs['cwd'] = str(self._root)
        kwargs['shell'] = True
        kwargs['text'] = True
        kwargs.setdefault('capture_output', True)

        result = subprocess.run(cmd, **kwargs)
        return {
            "code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    def read_file(self, rel_path: Union[str, Path]) -> str:
        """
        Safely read a file within the target directory.

        Args:
            rel_path: Relative path to the file

        Returns:
            File contents as string
        """
        safe_path = self.safe_path(rel_path)
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_file(self, rel_path: Union[str, Path], content: str) -> None:
        """
        Safely write a file within the target directory.

        Args:
            rel_path: Relative path to the file
            content: Content to write
        """
        safe_path = self.safe_path(rel_path)
        # Ensure parent directory exists
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def list_files(self, pattern: str = "**/*.py") -> List[Path]:
        """
        List files matching a pattern within the target directory.

        Args:
            pattern: Glob pattern (e.g., "**/*.py", "src/**/*.js")

        Returns:
            List of absolute paths
        """
        # First try git ls-files (respects .gitignore)
        result = self.safe_cmd("git ls-files")
        if result['code'] == 0:
            files = []
            for line in result['stdout'].splitlines():
                if line.strip():
                    files.append(self._root / line.strip())
            return files

        # Fallback to glob
        return list(self._root.glob(pattern))

    def file_exists(self, rel_path: Union[str, Path]) -> bool:
        """Check if a file exists within the target directory."""
        try:
            return self.safe_path(rel_path).exists()
        except TargetSecurityError:
            return False

    def mkdir(self, rel_path: Union[str, Path]) -> Path:
        """Create a directory within the target."""
        safe_path = self.safe_path(rel_path)
        safe_path.mkdir(parents=True, exist_ok=True)
        return safe_path

    @property
    def root(self) -> Path:
        """Get the target root directory."""
        return self._root

    @property
    def cc_dir(self) -> Path:
        """Get the .cc directory within the target."""
        return self._root / ".cc"

    @property
    def workspace_file(self) -> Path:
        """Get the workspace.json file path."""
        return self.cc_dir / "workspace.json"

    @property
    def agents_dir(self) -> Path:
        """Get the agents directory within .cc"""
        return self.cc_dir / "agents"

    def __repr__(self) -> str:
        return f"TargetContext({self._root})"

    def __str__(self) -> str:
        return str(self._root)
