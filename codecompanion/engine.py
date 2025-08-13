import subprocess
import os
import hashlib


def run_cmd(cmd: str):
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return {"code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def apply_patch(patch_text: str):
    # Try apply unified diff
    tmp = ".cc/.tmp.patch"
    os.makedirs(".cc", exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(patch_text)
    r = run_cmd(f"git apply -p0 {tmp}")  # first try
    if r["code"] != 0:
        r = run_cmd(f"git apply -p0 -3 {tmp}")  # fallback with 3-way
    return r


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:8]


def load_repo_map(root="."):
    out = run_cmd("git ls-files")
    files = out["stdout"].splitlines() if out["code"] == 0 else []
    return files
