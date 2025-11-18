import os
import sys
import json
import argparse
from .bootstrap import ensure_bootstrap
from . import __version__
from .repl import chat_repl
from .runner import run_pipeline, run_single_agent
from .info_core import gather_all_info


def main():
    parser = argparse.ArgumentParser(
        prog="codecompanion",
        description="CodeCompanion – standalone agent runner & chat REPL (OpenRouter-backed).",
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")
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
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    # Handle --info command
    if args.info:
        project_root = os.getcwd()
        info_data = gather_all_info(project_root)

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

    info = ensure_bootstrap()
    if args.check:
        print("[codecompanion] OK. Bootstrap dir:", info["dir"])
        if info["created"]:
            print("[codecompanion] Created:", ", ".join(info["created"]))
        print("[codecompanion] Agents dir:", info["agents_dir"])
        print("[codecompanion] Provider:", args.provider)
        return 0

    if args.chat:
        return chat_repl(provider=args.provider)
    if args.auto:
        return run_pipeline(provider=args.provider)
    if args.run:
        return run_single_agent(args.run, provider=args.provider)
    # default help
    parser.print_help()
    return 0
