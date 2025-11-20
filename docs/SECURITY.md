# CodeCompanion Security Model

## Overview

CodeCompanion Phase 0 implements a security-first architecture using the **TargetContext** isolation model. This ensures that CodeCompanion can safely operate on arbitrary repositories without risking system integrity or data leakage.

## Core Security Principles

### 1. Target Isolation

All file operations and subprocess calls are scoped to a designated target directory through the `TargetContext` class.

**What this prevents:**
- Path traversal attacks (`../../etc/passwd`)
- Accidental modification of system directories
- Operations escaping the target repository
- Cross-project data leakage

**How it works:**
```python
from codecompanion.target import TargetContext

# Create a secure context
target = TargetContext("/home/user/my-project")

# All operations stay within bounds
target.safe_path("src/main.py")           # ✅ OK
target.safe_path("../../etc/passwd")      # ❌ Raises TargetSecurityError
```

### 2. Forbidden Directories

CodeCompanion explicitly rejects operation on critical system directories:

**Blocked paths:**
- `/` - System root
- `/usr`, `/etc`, `/bin`, `/sbin` - System directories
- `/var`, `/boot`, `/sys`, `/proc`, `/dev` - Special filesystems
- User home directory itself (projects within home are allowed)

**Example:**
```bash
codecompanion --auto                    # ✅ Works in /home/user/my-project
cd / && codecompanion --auto           # ❌ Fails with security error
```

### 3. Symlink Resolution

All paths are resolved through symlinks before validation to prevent symlink-based escapes.

**Attack prevented:**
```bash
# Attacker creates malicious symlink
ln -s /etc/passwd ./innocent_file

# CodeCompanion resolves the symlink and rejects it
target.safe_path("innocent_file")  # ❌ Raises TargetSecurityError
```

### 4. Subprocess Containment

All subprocess calls (`git`, `pytest`, `pip`, etc.) are executed with `cwd` forced to the target directory.

**What this prevents:**
- Commands accessing files outside target
- Shell injection via path manipulation
- Accidental operations on wrong repository

```python
# Before (Phase 0): Unsafe
subprocess.run("git status", shell=True)  # Runs anywhere

# After (Phase 0): Safe
target.safe_cmd("git status")  # Always runs in target.root
```

## Security Boundaries

### What TargetContext Protects Against

| Attack Vector | Protection | How |
|--------------|------------|-----|
| Path traversal | ✅ Yes | `safe_path()` validates all paths |
| Symlink escape | ✅ Yes | Paths resolved before validation |
| System directory modification | ✅ Yes | Forbidden paths list |
| Cross-repo leakage | ✅ Yes | All ops scoped to target |
| Home directory corruption | ✅ Yes | Rejects `$HOME` itself |
| Shell injection via paths | ⚠️ Partial | Use `shlex.quote()` for args |

### What It Doesn't Protect (Yet)

| Risk | Status | Mitigation |
|------|--------|------------|
| Malicious code execution | ❌ No sandbox | Don't run untrusted code |
| API key leakage | ❌ Not addressed | Use env vars, not files |
| Network attacks | ❌ Not addressed | Review LLM-generated code |
| Resource exhaustion | ❌ Not addressed | Monitor agent runs |

## Usage Guidelines

### Safe Practices

1. **Always use TargetContext for new code:**
   ```python
   # Good
   def my_agent(provider, target: TargetContext):
       files = target.list_files()

   # Bad (deprecated)
   def my_agent(provider):
       files = os.listdir(".")
   ```

2. **Validate user inputs:**
   ```python
   from codecompanion.security import sanitize_filename

   user_input = request.get("filename")
   safe_name = sanitize_filename(user_input)
   target.write_file(safe_name, content)
   ```

3. **Use dedicated security utilities:**
   ```python
   from codecompanion.security import (
       is_safe_git_branch_name,
       sanitize_command_arg,
       validate_api_key_format
   )
   ```

### Unsafe Practices to Avoid

1. **Never bypass TargetContext:**
   ```python
   # NEVER DO THIS
   with open(f"{target.root}/file.txt") as f:  # ❌ Bypasses validation
       ...

   # DO THIS INSTEAD
   content = target.read_file("file.txt")      # ✅ Safe
   ```

2. **Never trust relative paths without validation:**
   ```python
   # NEVER DO THIS
   user_path = "../../../etc/passwd"
   os.remove(user_path)  # ❌ Path traversal

   # DO THIS INSTEAD
   safe_path = target.safe_path(user_path)  # ✅ Raises error
   ```

3. **Never use `shell=True` without sanitizing:**
   ```python
   # DANGEROUS
   subprocess.run(f"git commit -m '{user_message}'", shell=True)

   # SAFER
   from codecompanion.security import sanitize_command_arg
   safe_msg = sanitize_command_arg(user_message)
   target.safe_cmd(f"git commit -m {safe_msg}")
   ```

## Testing Security

### Running Security Tests

```bash
# Run the full security test suite
pytest tests/test_target_security.py -v

# Run specific security tests
pytest tests/test_target_security.py::TestTargetContext::test_rejects_path_traversal -v
```

### Expected Test Coverage

Phase 0 security tests cover:
- ✅ Path traversal rejection (15+ test cases)
- ✅ System directory blocking (5+ test cases)
- ✅ Symlink attack prevention
- ✅ Subprocess containment
- ✅ File operation validation
- ✅ Input sanitization utilities

**Coverage goal:** >95% for `target.py` and `security.py`

## Security Checklist for New Features

When adding new functionality, verify:

- [ ] All file operations use `TargetContext` methods
- [ ] No direct `open()`, `os.path.*`, or `Path()` operations
- [ ] All subprocesses go through `target.safe_cmd()`
- [ ] User inputs sanitized with `security.py` utilities
- [ ] Added tests to `test_target_security.py`
- [ ] No hardcoded paths or assumptions about directory structure
- [ ] Error messages don't leak sensitive path information

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** open a public issue
2. Email security details to the maintainer
3. Include:
   - Vulnerability description
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Future Security Enhancements

Planned for future phases:

- **Phase 1:** API key management with secret storage
- **Phase 2:** Sandboxed code execution for LLM-generated code
- **Phase 3:** Network request filtering and monitoring
- **Phase 4:** Resource limits (CPU, memory, disk)

## References

- **TargetContext API:** `codecompanion/target.py`
- **Security Utilities:** `codecompanion/security.py`
- **Test Suite:** `tests/test_target_security.py`
- **Path Validation:** PEP 428 (pathlib), PEP 519 (PathLike)

---

**Last Updated:** Phase 0 (Security Foundation)
**Security Model Version:** 0.1.0
