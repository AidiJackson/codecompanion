import os
import sys
import json
import argparse
import logging

# Suppress Streamlit and other verbose logging early
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('streamlit.logger').setLevel(logging.ERROR)
os.environ['STREAMLIT_LOGGER_LEVEL'] = 'error'

from .bootstrap import ensure_bootstrap
from .target import TargetContext
from . import __version__
from .repl import chat_repl
from .runner import run_pipeline, run_single_agent
from .info_core import gather_all_info


def main():
    parser = argparse.ArgumentParser(
        prog="codecompanion",
        description="""
CodeCompanion - Repo-Agnostic AI Development Assistant

Runs specialized AI agents on any codebase with secure target isolation.
Automatically detects project type and optimizes agent workflows.
        """,
        epilog="""
Examples:
  codecompanion --init                      Initialize in current repository
  codecompanion --check                     Verify installation and config
  codecompanion --auto                      Run full 9-agent pipeline
  codecompanion --run Analyzer              Run single agent
  codecompanion --task "fix import errors"  Natural language task
  codecompanion detect                      Show project type detection
  codecompanion --dashboard                 Launch web UI
  codecompanion --info                      Show system status

Available Agents:
  Installer, EnvDoctor, Analyzer, DepAuditor, BugTriage,
  Fixer, TestRunner, WebDoctor, PRPreparer

Learn more: https://github.com/AidiJackson/codecompanion
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize CodeCompanion in current repository",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check environment and bootstrap presence, then exit",
    )
    parser.add_argument("--chat", action="store_true", help="Start chat REPL")
    parser.add_argument(
        "--auto", action="store_true", help="Run full 10-agent pipeline"
    )
    parser.add_argument("--run", metavar="AGENT", help="Run a single agent by name")
    parser.add_argument(
        "--provider",
        default=os.getenv("CC_PROVIDER", "claude"),
        help="LLM provider (claude, gpt4, gemini)",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Start the Control Tower web dashboard",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Display system information (use --raw for JSON output)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw JSON format (used with --info)",
    )
    parser.add_argument(
        "--task",
        metavar="DESCRIPTION",
        help="Natural language task description (runs Orchestrator + relevant agents)",
    )

    # Subcommands (detect, etc.)
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')

    detect_parser = subparsers.add_parser(
        'detect',
        help='Detect project type and show recommendations'
    )

    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    # Handle --init command
    if args.init:
        from .workspace import (
            create_workspace_config,
            save_workspace_config,
            is_initialized,
            get_workspace_summary
        )
        from .target import TargetSecurityError

        try:
            target = TargetContext(os.getcwd())

            # Check if already initialized
            already_initialized = is_initialized(target)

            # Run bootstrap to ensure .cc/ structure
            info = ensure_bootstrap(target)

            # Create/update workspace configuration
            workspace_config = create_workspace_config(target, force=False)
            save_workspace_config(target, workspace_config)

            # Display success message
            if already_initialized:
                print("ℹ️  CodeCompanion workspace updated")
            else:
                print("✅ CodeCompanion initialized successfully!")

            print(f"\n📁 Target: {target.root}")
            print()
            print(get_workspace_summary(workspace_config))

            print("\n💡 Next steps:")
            print("   codecompanion --check        # Verify installation")
            print("   codecompanion --auto         # Run full pipeline")
            print("   codecompanion --run Analyzer # Run single agent")

            return 0

        except TargetSecurityError as e:
            print(f"❌ Security error: {e}")
            print("\n💡 Tip: CodeCompanion cannot operate on system directories.")
            print("   Please run this command from within a project directory.")
            return 1
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    # Handle --info command
    if args.info:
        project_root = os.getcwd()
        target = TargetContext(project_root)
        info_data = gather_all_info(str(target.root))

        if args.raw:
            # Raw JSON output
            print(json.dumps(info_data, indent=2))
        else:
            # Human-readable output
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel

            console = Console()

            # Bootstrap section
            console.print("\n[bold cyan]Project Status[/bold cyan]")
            console.print(f"  Root: {info_data['bootstrap']['root']}")
            console.print(f"  Status: {info_data['bootstrap']['status']}")
            console.print(f"  Config Dir: {info_data['bootstrap']['cc_dir']}")

            # Agent workflow section
            console.print("\n[bold cyan]Agent Workflow[/bold cyan]")
            console.print(f"  Completion: {info_data['agent_workflow']['completion']}")
            console.print(f"  Agents Dir: {info_data['agent_workflow']['agents_dir']}")

            # Providers section
            console.print("\n[bold cyan]LLM Providers[/bold cyan]")
            provider_table = Table(show_header=True)
            provider_table.add_column("Provider")
            provider_table.add_column("Model")
            provider_table.add_column("Status")

            for provider in info_data['providers']:
                status = "[green]✓ Configured[/green]" if provider['api_key_set'] else "[red]✗ Missing Key[/red]"
                provider_table.add_row(provider['name'], provider['model'], status)

            console.print(provider_table)

            # Pipeline section
            console.print("\n[bold cyan]Pipeline Status[/bold cyan]")
            pipeline = info_data['pipeline']
            console.print(f"  Status: {pipeline['status']}")
            console.print(f"  Total Runs: {pipeline['total_runs']}")
            if pipeline['last_run']:
                console.print(f"  Last Run: {pipeline['last_run']['timestamp']}")
                console.print(f"  Last Status: {pipeline['last_run']['status']}")
                console.print(f"  Summary: {pipeline['last_run']['summary']}")
            else:
                console.print("  Last Run: Never")
            if pipeline['success_rate']:
                console.print(f"  Success Rate: {pipeline['success_rate']}")

            # Errors section
            console.print("\n[bold cyan]Errors & Recovery[/bold cyan]")
            errors = info_data['errors']
            console.print(f"  Total Errors: {errors['total_errors']}")
            console.print(f"  Unrecovered: {errors['unrecovered_errors']}")
            if errors['recent']:
                console.print("  Recent Errors:")
                for err in errors['recent']:
                    status_marker = "✓" if err['recovered'] else "✗"
                    console.print(f"    [{status_marker}] {err['timestamp']} - {err['agent']} ({err['stage']}): {err['message']}")
            else:
                console.print("  No errors recorded")

            # Recommendations section
            if info_data['recommendations']:
                console.print("\n[bold yellow]Recommendations[/bold yellow]")
                for rec in info_data['recommendations']:
                    console.print(f"  • {rec['message']}")
                    console.print(f"    → {rec['action']}")
            else:
                console.print("\n[bold green]✓ System appears healthy[/bold green]")

        return 0

    # Handle --dashboard command
    if args.dashboard:
        from .dashboard.app import run_dashboard
        run_dashboard()
        return 0

    # Handle detect subcommand
    if args.command == 'detect':
        from .project_detector import ProjectDetector
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        target = TargetContext(os.getcwd())
        info = ProjectDetector.detect_project_type(target.root)
        preset = ProjectDetector.get_recommended_preset(info)

        console = Console()

        # Project detection panel
        console.print(Panel.fit(
            f"[cyan]Type:[/cyan] {info['type']}\n"
            f"[cyan]Language:[/cyan] {info.get('language', 'unknown')}\n"
            f"[cyan]Framework:[/cyan] {info.get('framework', 'none')}\n"
            f"[cyan]Confidence:[/cyan] {info['confidence']:.0%}",
            title="📦 Project Detection",
            border_style="blue"
        ))

        # Recommended preset
        console.print("\n[bold cyan]Recommended Agent Preset[/bold cyan]")
        console.print(f"  {preset['description']}")
        console.print(f"\n[bold cyan]Focus Areas[/bold cyan]")
        console.print(f"  {preset['focus']}")
        console.print(f"\n[bold cyan]Suggested Agents[/bold cyan]")
        for i, agent in enumerate(preset['agents'], 1):
            console.print(f"  {i}. {agent}")

        console.print("\n[bold green]💡 Tip:[/bold green] Run [cyan]codecompanion --auto[/cyan] to execute this preset")

        return 0

    # Handle --task command
    if args.task:
        from .task_handler import run_task

        try:
            target = TargetContext(os.getcwd())
            return run_task(args.task, target, provider=args.provider)
        except Exception as e:
            print(f"❌ Task execution failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    # Create target context for current directory
    target = TargetContext(os.getcwd())

    info = ensure_bootstrap(target)
    if args.check:
        print("[codecompanion] OK. Bootstrap dir:", info["dir"])
        if info["created"]:
            print("[codecompanion] Created:", ", ".join(info["created"]))
        print("[codecompanion] Agents dir:", info["agents_dir"])
        print("[codecompanion] Target:", target.root)
        print("[codecompanion] Provider:", args.provider)
        return 0

    if args.chat:
        return chat_repl(provider=args.provider)
    if args.auto:
        return run_pipeline(provider=args.provider, target=target)
    if args.run:
        return run_single_agent(args.run, provider=args.provider, target=target)
    # default help
    parser.print_help()
    return 0
