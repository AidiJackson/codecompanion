import subprocess
import os
import hashlib
from typing import Optional
from .target import TargetContext


def run_cmd(cmd: str, target: Optional[TargetContext] = None):
    """
    Execute a shell command, optionally within a TargetContext.

    Args:
        cmd: Command to execute
        target: Optional TargetContext for secure execution

    Returns:
        dict with 'code', 'stdout', 'stderr' keys
    """
    if target:
        return target.safe_cmd(cmd)
    else:
        # Fallback for backward compatibility
        p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        return {"code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def apply_patch(patch_text: str, target: Optional[TargetContext] = None):
    """
    Apply a git patch within a target context.

    Args:
        patch_text: Patch content in unified diff format
        target: Optional TargetContext for secure patching

    Returns:
        dict with result of git apply command
    """
    if target:
        # Use target context for secure operation
        tmp_path = target.cc_dir / ".tmp.patch"
        target.mkdir(".cc")  # Ensure .cc exists
        target.write_file(".cc/.tmp.patch", patch_text)

        # Try apply with target context
        r = target.safe_cmd(f"git apply -p0 {tmp_path}")
        if r["code"] != 0:
            r = target.safe_cmd(f"git apply -p0 -3 {tmp_path}")
        return r
    else:
        # Fallback for backward compatibility
        tmp = ".cc/.tmp.patch"
        os.makedirs(".cc", exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(patch_text)
        r = run_cmd(f"git apply -p0 {tmp}")
        if r["code"] != 0:
            r = run_cmd(f"git apply -p0 -3 {tmp}")
        return r


def file_hash(path: str, target: Optional[TargetContext] = None):
    """
    Calculate SHA256 hash of a file.

    Args:
        path: Path to file (relative if target provided, absolute otherwise)
        target: Optional TargetContext for secure file access

    Returns:
        First 8 characters of hex digest
    """
    h = hashlib.sha256()

    if target:
        content = target.read_file(path)
        h.update(content.encode('utf-8'))
    else:
        # Fallback for backward compatibility
        with open(path, "rb") as f:
            h.update(f.read())

    return h.hexdigest()[:8]


def load_repo_map(target: Optional[TargetContext] = None):
    """
    Load list of tracked files in the repository.

    Args:
        target: Optional TargetContext for secure git operation

    Returns:
        List of file paths
    """
    if target:
        return [str(f.relative_to(target.root)) for f in target.list_files()]
    else:
        # Fallback for backward compatibility
        out = run_cmd("git ls-files")
        files = out["stdout"].splitlines() if out["code"] == 0 else []
        return files
