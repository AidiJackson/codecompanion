from pathlib import Path


def detect_project_type():
    path = Path(".")

    if (path / "package.json").exists():
        return {"type": "node", "framework": "javascript"}
    elif any((path / f).exists() for f in ["requirements.txt", "pyproject.toml"]):
        return {"type": "python", "framework": "python"}
    elif (path / "Cargo.toml").exists():
        return {"type": "rust", "framework": "rust"}
    else:
        return {"type": "generic", "framework": "unknown"}


def detect_and_configure():
    info = detect_project_type()
    print(f"🔍 Project type: {info['type']}")
    print(f"🎯 Framework: {info['framework']}")
    print("🤖 Recommended: codecompanion --auto")
    return info
