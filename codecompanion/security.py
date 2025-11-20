"""
Security validation utilities for CodeCompanion.

Provides helper functions for validating paths, commands, and user input
to prevent security vulnerabilities.
"""
import re
import shlex
from pathlib import Path
from typing import Optional


def is_system_directory(path: Path) -> bool:
    """
    Check if a path is a critical system directory.

    Args:
        path: Path to check

    Returns:
        True if path is a system directory that should not be modified
    """
    system_dirs = [
        Path("/"),
        Path("/usr"),
        Path("/etc"),
        Path("/bin"),
        Path("/sbin"),
        Path("/var"),
        Path("/boot"),
        Path("/sys"),
        Path("/proc"),
        Path("/dev"),
    ]

    resolved = path.resolve()
    for sys_dir in system_dirs:
        if resolved == sys_dir:
            return True
        # Check if it's a direct child of a protected dir (but allow deeper nesting)
        if sys_dir in [Path("/"), Path("/home"), Path("/root")]:
            continue
        try:
            if resolved.is_relative_to(sys_dir):
                return True
        except (ValueError, TypeError):
            pass

    return False


def is_safe_directory(path: Path) -> bool:
    """
    Comprehensive safety check for a directory path.

    Args:
        path: Path to validate

    Returns:
        True if the path is safe to use as a target directory
    """
    # Must exist
    if not path.exists():
        return False

    # Must be a directory
    if not path.is_dir():
        return False

    # Must not be a system directory
    if is_system_directory(path):
        return False

    # Should not be the user's home directory itself
    try:
        if path.resolve() == Path.home():
            return False
    except (RuntimeError, KeyError):
        pass

    return True


def validate_no_path_traversal(base: Path, candidate: Path) -> None:
    """
    Validate that a candidate path doesn't escape the base directory.

    Args:
        base: Base directory that should contain the candidate
        candidate: Path to validate

    Raises:
        ValueError: If candidate escapes base directory
    """
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()

    try:
        candidate_resolved.relative_to(base_resolved)
    except ValueError:
        raise ValueError(
            f"Path traversal detected: {candidate} would escape {base}"
        )


def sanitize_filename(filename: str, allow_path_separators: bool = False) -> str:
    """
    Sanitize a filename to prevent directory traversal and injection.

    Args:
        filename: Original filename
        allow_path_separators: Whether to allow / in the filename

    Returns:
        Sanitized filename
    """
    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Remove or reject path traversal attempts
    if not allow_path_separators:
        # Remove all path separators
        filename = filename.replace('/', '_').replace('\\', '_')

    # Remove dangerous patterns
    filename = filename.replace('..', '')

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def sanitize_command_arg(arg: str) -> str:
    """
    Sanitize a command line argument to prevent injection.

    Note: This is a basic sanitizer. For full safety, avoid shell=True
    and use subprocess with argument lists instead.

    Args:
        arg: Command argument to sanitize

    Returns:
        Sanitized argument (quoted if necessary)
    """
    # Use shlex.quote for proper shell escaping
    return shlex.quote(arg)


def is_safe_git_branch_name(branch_name: str) -> bool:
    """
    Validate that a branch name is safe and follows git conventions.

    Args:
        branch_name: Branch name to validate

    Returns:
        True if branch name is valid and safe
    """
    # Git branch name rules:
    # - No spaces
    # - No special shell characters
    # - No .., .lock suffix
    # - No starting with -
    # - No control characters

    if not branch_name:
        return False

    # Check for dangerous patterns
    dangerous_patterns = [
        r'\.\.',  # Path traversal
        r'\.lock$',  # Git lockfiles
        r'^\.',  # Hidden files
        r'^-',  # Looks like a flag
        r'\s',  # Whitespace
        r'[;&|`$()]',  # Shell metacharacters
        r'[\x00-\x1f]',  # Control characters
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, branch_name):
            return False

    # Must contain only safe characters
    if not re.match(r'^[a-zA-Z0-9/_-]+$', branch_name):
        return False

    return True


def validate_api_key_format(api_key: str, provider: str) -> bool:
    """
    Basic validation of API key format (doesn't verify if key works).

    Args:
        api_key: API key to validate
        provider: Provider name (anthropic, openai, etc.)

    Returns:
        True if key format looks valid
    """
    if not api_key or len(api_key) < 10:
        return False

    # Provider-specific format checks
    if provider.lower() in ['anthropic', 'claude']:
        # Anthropic keys typically start with sk-ant-
        return api_key.startswith('sk-ant-')
    elif provider.lower() in ['openai', 'gpt', 'gpt4']:
        # OpenAI keys typically start with sk-
        return api_key.startswith('sk-')
    elif provider.lower() == 'gemini':
        # Google API keys are typically long alphanumeric strings
        return len(api_key) >= 30 and api_key.isalnum()
    elif provider.lower() == 'openrouter':
        # OpenRouter keys start with sk-or-
        return api_key.startswith('sk-or-')

    # Unknown provider - do basic check
    return len(api_key) >= 20


def is_safe_url(url: str) -> bool:
    """
    Basic check if a URL is safe to fetch.

    Args:
        url: URL to validate

    Returns:
        True if URL appears safe
    """
    # Must start with http:// or https://
    if not (url.startswith('http://') or url.startswith('https://')):
        return False

    # Block localhost and private IPs (basic check)
    dangerous_hosts = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '[::]',
        '::1',
    ]

    url_lower = url.lower()
    for host in dangerous_hosts:
        if f'//{host}' in url_lower or f'//{host}:' in url_lower:
            return False

    return True
