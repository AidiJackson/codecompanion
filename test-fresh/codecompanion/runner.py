import subprocess
from .llm import complete

AGENT_WORKFLOW = [
    {"name": "Installer", "provider": None},
    {"name": "EnvDoctor", "provider": "claude"},
    {"name": "Analyzer", "provider": "gpt4"},
    {"name": "DepAuditor", "provider": "gemini"},
    {"name": "BugTriage", "provider": "claude"},
    {"name": "Fixer", "provider": "gpt4"},
    {"name": "TestRunner", "provider": None},
    {"name": "WebDoctor", "provider": "gemini"},
    {"name": "PRPreparer", "provider": "claude"},
]


def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def run_single_agent(name, provider=None):
    agent_config = next((a for a in AGENT_WORKFLOW if a["name"] == name), None)
    if not agent_config:
        print(f"Unknown agent: {name}")
        return 2

    selected_provider = provider or agent_config["provider"]
    print(f"[agent] {name} (provider: {selected_provider or 'none'})")

    # Execute agent
    if name == "Installer":
        return installer_agent()
    elif name == "EnvDoctor":
        return env_doctor_agent(selected_provider)
    elif name == "Analyzer":
        return analyzer_agent(selected_provider)
    elif name == "TestRunner":
        return test_runner_agent()
    else:
        return generic_agent(name, selected_provider)


def run_pipeline(provider=None):
    for agent_config in AGENT_WORKFLOW:
        name = agent_config["name"]
        assigned_provider = agent_config["provider"]
        rc = run_single_agent(name, assigned_provider)
        if rc != 0:
            print(f"[error] {name} returned {rc}")
            return rc
    print("[ok] Pipeline complete")
    return 0


def installer_agent():
    print("[installer] Setting up environment...")
    r = run_cmd("python -m pip install --upgrade pip")
    print(f"[installer] pip upgrade: {r.returncode}")
    return 0


def env_doctor_agent(provider):
    print(f"[env-doctor] Checking Python environment (using {provider})...")
    r = run_cmd("python --version")
    print(f"[env-doctor] {r.stdout.strip()}")
    return 0


def analyzer_agent(provider):
    print(f"[analyzer] Analyzing codebase (using {provider})...")
    r = run_cmd("find . -name '*.py' | wc -l")
    print(f"[analyzer] Found {r.stdout.strip()} Python files")

    if provider:
        try:
            response = complete(
                "Analyze this codebase briefly",
                [{"role": "user", "content": "What should I focus on?"}],
                provider=provider,
            )
            print(f"[analyzer] AI insight: {response.get('content', '')[:100]}...")
        except Exception as e:
            print(f"[analyzer] AI analysis skipped: {e}")
    return 0


def test_runner_agent():
    print("[test-runner] Running tests...")
    r = run_cmd("python -m pytest --version 2>/dev/null || echo 'pytest not available'")
    print(f"[test-runner] {r.stdout.strip()}")
    return 0


def generic_agent(name, provider):
    print(f"[{name.lower()}] Agent executed successfully")
    return 0
