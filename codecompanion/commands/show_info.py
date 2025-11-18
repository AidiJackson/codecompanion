from __future__ import annotations

import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..info_core import gather_info_snapshot


def show_info_command(raw: bool = False, project_root: str = ".") -> None:
    """
    Display CodeCompanion system information.

    Args:
        raw: If True, output raw JSON. If False, output formatted panel.
        project_root: Project root directory (default: current directory)
    """
    snapshot = gather_info_snapshot(project_root)
    data = snapshot.raw

    if raw:
        # Print raw JSON
        print(json.dumps(data, indent=2))
    else:
        # Render human-readable panel
        _render_info_panel(data)


def _render_info_panel(data: dict) -> None:
    """Render a rich formatted info panel."""
    console = Console()

    console.print("\n[bold cyan]CodeCompanion Control Tower[/bold cyan]")
    console.print("[dim]Multi-agent development OS status[/dim]\n")

    # Bootstrap section
    bootstrap = data.get("bootstrap", {})
    console.print(Panel(
        f"[bold]Project Root:[/bold] {bootstrap.get('project_root', 'N/A')}\n"
        f"[bold]CC Directory:[/bold] {bootstrap.get('cc_dir', 'N/A')}\n"
        f"[bold]Agents Directory:[/bold] {bootstrap.get('agents_dir', 'N/A')}\n"
        f"[bold]Status:[/bold] {bootstrap.get('status', 'N/A')}",
        title="[bold]Project / Bootstrap[/bold]",
        border_style="green",
    ))

    # Agent files section
    agent_files = data.get("agent_files", [])
    if agent_files:
        files_table = Table(title="Agent Files", show_header=True, header_style="bold magenta")
        files_table.add_column("Agent File", style="cyan")
        files_table.add_column("Exists", justify="center")
        files_table.add_column("Size", justify="right")
        files_table.add_column("Status", justify="center")

        for file_info in agent_files:
            exists_str = "✓" if file_info.get("exists") else "✗"
            size_str = f"{file_info.get('size_bytes', 0)} bytes"
            status = "stub" if file_info.get("is_stub") else "custom"
            files_table.add_row(
                file_info.get("name", ""),
                exists_str,
                size_str,
                status,
            )

        console.print(files_table)
        console.print()

    # Agent workflow section
    agent_workflow = data.get("agent_workflow", [])
    if agent_workflow:
        workflow_table = Table(title="Agent Workflow", show_header=True, header_style="bold magenta")
        workflow_table.add_column("Agent", style="cyan")
        workflow_table.add_column("Provider", style="yellow")
        workflow_table.add_column("Model", style="green")

        for agent in agent_workflow:
            workflow_table.add_row(
                agent.get("name", ""),
                agent.get("provider", "-"),
                agent.get("model", "-") or "-",
            )

        console.print(workflow_table)
        console.print()

    # Providers section
    providers = data.get("providers", [])
    if providers:
        providers_table = Table(title="Provider Configuration", show_header=True, header_style="bold magenta")
        providers_table.add_column("Provider", style="cyan")
        providers_table.add_column("API Key Env", style="yellow")
        providers_table.add_column("Key Set", justify="center")
        providers_table.add_column("Model", style="green")

        for provider in providers:
            key_set = "✓" if provider.get("api_key_set") else "✗"
            providers_table.add_row(
                provider.get("name", ""),
                provider.get("api_key_env", ""),
                key_set,
                provider.get("model", "-"),
            )

        console.print(providers_table)
        console.print()

    # Pipeline status section
    pipeline = data.get("pipeline_status", {})
    console.print(Panel(
        f"[bold]Last Run:[/bold] {pipeline.get('last_run', 'Never')}\n"
        f"[bold]Status:[/bold] {pipeline.get('status', 'N/A')}\n"
        f"[bold]Agents Completed:[/bold] {pipeline.get('agents_completed', 0)}\n"
        f"[bold]Agents Failed:[/bold] {pipeline.get('agents_failed', 0)}",
        title="[bold]Pipeline Status[/bold]",
        border_style="blue",
    ))

    # Fail path section
    fail_path = data.get("fail_path", {})
    console.print(Panel(
        f"[bold]Enabled:[/bold] {fail_path.get('enabled', False)}\n"
        f"[bold]Failure Log:[/bold] {fail_path.get('failure_log', 'None')}\n"
        f"[bold]Self-Repair Attempts:[/bold] {fail_path.get('self_repair_attempts', 0)}",
        title="[bold]Fail-Path & Self-Repair[/bold]",
        border_style="yellow",
    ))

    # Errors section
    errors = data.get("errors", [])
    if errors:
        console.print("\n[bold red]Recent Errors:[/bold red]")
        for error in errors:
            console.print(f"  • {error}")
    else:
        console.print("\n[bold green]No recent errors[/bold green]")

    # Recommendations section
    recommendations = data.get("recommendations", [])
    if recommendations:
        console.print("\n[bold yellow]Recommendations:[/bold yellow]")
        for rec in recommendations:
            severity = rec.get("severity", "info")
            message = rec.get("message", "")
            action = rec.get("action", "")

            severity_color = {
                "error": "red",
                "warning": "yellow",
                "info": "cyan",
            }.get(severity, "white")

            console.print(f"  [{severity_color}]•[/{severity_color}] {message}")
            if action:
                console.print(f"    [dim]→ {action}[/dim]")
    else:
        console.print("\n[bold green]No recommendations[/bold green]")

    console.print()
