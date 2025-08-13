#!/usr/bin/env python3
"""
CodeCompanion universal installer (Replit/Nix-safe)

- Creates a local virtualenv in .ccenv (if not present)
- Installs CodeCompanion from GitHub into that venv
- Drops a ./cc launcher that runs the installed CLI
- Works in Replit's externally-managed Python (PEP 668) without --break-system-packages
"""

import os
import sys
import subprocess
import shutil
import platform

REPO_URL = "https://github.com/AidiJackson/codecompanion.git"  # your repo
REPO_REF = "main"                                             # branch or tag
VENV_DIR = ".ccenv"

def run(cmd, check=True):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)

def bin_path(venv_dir: str, exe: str) -> str:
    if platform.system().lower().startswith("win"):
        return os.path.join(venv_dir, "Scripts", exe + ".exe")
    return os.path.join(venv_dir, "bin", exe)

def ensure_venv():
    if os.path.isdir(VENV_DIR) and os.path.exists(bin_path(VENV_DIR, "python")):
        print(f"✅ Using existing virtualenv: {VENV_DIR}")
        return
    print(f"📦 Creating virtualenv: {VENV_DIR}")
    run([sys.executable, "-m", "venv", VENV_DIR])
    py = bin_path(VENV_DIR, "python")
    # Upgrade packaging tools
    run([py, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

def install_package():
    pip = bin_path(VENV_DIR, "pip")
    print("📦 Installing CodeCompanion from GitHub…")
    run([pip, "install", "--upgrade", f"git+{REPO_URL}@{REPO_REF}"])

def write_launcher():
    launcher = os.path.abspath("./cc")
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f'VENV_DIR="{os.path.abspath(VENV_DIR)}"',
        'BIN_DIR="$VENV_DIR/bin"',
        'if [ ! -x "$BIN_DIR/python" ]; then',
        '  echo "Error: virtualenv not found. Run installer again." >&2',
        '  exit 1',
        "fi",
        "",
        "# Map short commands to CLI flags",
        'case "${1:-}" in',
        '  check)   set -- --check ;;',
        '  auto)    set -- --auto ;;',
        '  detect)  set -- --detect ;;',
        '  run)     shift; set -- --run "$@" ;;',
        '  chat)    set -- --chat ;;',
        'esac',
        "",
        "# Prefer installed console script if available",
        'if [ -x "$BIN_DIR/codecompanion" ]; then',
        '  exec "$BIN_DIR/codecompanion" "$@"',
        'elif [ -x "$BIN_DIR/cc" ]; then',
        '  exec "$BIN_DIR/cc" "$@"',
        'else',
        '  exec "$BIN_DIR/python" -m cc_cli.main "$@"',
        'fi',
    ]
    with open(launcher, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(launcher, 0o755)
    print("✅ Launcher created: ./cc")

def print_success():
    print("\n🎉 Installation complete.")
    print("Try:")
    print("  codecompanion --check     # if the console script name is exposed")
    print("  ./cc detect               # wrapper that always works")
    print("  ./cc auto                 # your 9-agent pipeline")
    print("\nUpgrade later with:")
    print(f'  {bin_path(VENV_DIR, "pip")} install --upgrade git+{REPO_URL}@{REPO_REF}')

def main():
    print(f"✅ Python {platform.python_version()}")
    try:
        ensure_venv()
        install_package()
        write_launcher()
        print_success()
    except subprocess.CalledProcessError as e:
        print("❌ Installation failed")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
