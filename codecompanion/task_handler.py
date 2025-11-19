"""
Natural language task handler using intelligent agent selection.

Provides a simple interface for users to describe tasks in natural language,
then automatically selects and runs the appropriate agents.
"""
from typing import Optional
from .target import TargetContext
from .runner import run_single_agent, AGENT_WORKFLOW


# Task keywords to agent mapping
TASK_AGENT_MAP = {
    # Environment and setup
    ("install", "setup", "dependencies", "requirements"): "Installer",
    ("environment", "env", "import", "runtime"): "EnvDoctor",

    # Analysis
    ("analyze", "analysis", "review", "inspect", "understand"): "Analyzer",
    ("structure", "architecture", "codebase"): "Analyzer",

    # Dependencies
    ("dependency", "dependencies", "package", "packages"): "DepAuditor",
    ("bloat", "unused", "redundant", "optimize"): "DepAuditor",

    # Debugging
    ("bug", "error", "failure", "broken", "failing"): "BugTriage",
    ("debug", "diagnose", "reproduce"): "BugTriage",

    # Fixes
    ("fix", "repair", "patch", "solve"): "Fixer",
    ("implement", "add", "create"): "Fixer",

    # Testing
    ("test", "testing", "coverage", "pytest"): "TestRunner",

    # Web apps
    ("web", "server", "api", "flask", "django", "fastapi"): "WebDoctor",
    ("streamlit", "webapp", "application"): "WebDoctor",

    # Git and PR
    ("commit", "pr", "pull request", "git"): "PRPreparer",
    ("documentation", "docs", "readme"): "PRPreparer",
}


def select_agent_for_task(task_description: str) -> str:
    """
    Select the most appropriate agent based on task description.

    Args:
        task_description: Natural language task description

    Returns:
        Agent name to run
    """
    task_lower = task_description.lower()

    # Check for keyword matches
    for keywords, agent in TASK_AGENT_MAP.items():
        if any(keyword in task_lower for keyword in keywords):
            return agent

    # Default to Analyzer for general tasks
    return "Analyzer"


def run_task(description: str, target: TargetContext, provider: str = "claude") -> int:
    """
    Execute a natural language task by selecting and running appropriate agent.

    Args:
        description: Task description in natural language
        target: TargetContext for the repository
        provider: LLM provider to use

    Returns:
        Exit code (0 = success)

    Examples:
        >>> run_task("Fix all import errors", target)
        >>> run_task("Analyze code structure", target)
        >>> run_task("Run tests with coverage", target)
    """
    # Select appropriate agent
    agent_name = select_agent_for_task(description)

    # Display what we're doing
    print(f"🎯 Task: {description}")
    print(f"📁 Target: {target.root}")
    print(f"🤖 Selected Agent: {agent_name}")
    print()

    # Run the selected agent
    return run_single_agent(agent_name, provider, target)


def get_task_suggestions() -> str:
    """
    Get suggestions for common tasks.

    Returns:
        Formatted string with task examples
    """
    return """
Common Tasks:

  Setup & Environment:
    - "Install dependencies"
    - "Fix import errors"
    - "Setup development environment"

  Analysis:
    - "Analyze code structure"
    - "Review codebase architecture"
    - "Find TODO comments"

  Dependencies:
    - "Optimize dependencies"
    - "Find unused packages"
    - "Audit dependencies for bloat"

  Debugging:
    - "Debug test failures"
    - "Reproduce bug"
    - "Find error root cause"

  Fixes:
    - "Fix type errors"
    - "Implement missing features"
    - "Patch security issues"

  Testing:
    - "Run tests with coverage"
    - "Create test suite"
    - "Check test failures"

  Web Apps:
    - "Setup Flask app"
    - "Configure API endpoints"
    - "Fix web server issues"

  Git & Documentation:
    - "Prepare for commit"
    - "Create pull request"
    - "Update documentation"
    """
