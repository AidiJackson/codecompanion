import os
import argparse
from .bootstrap import ensure_bootstrap
from . import __version__
from .repl import chat_repl
from .runner import run_pipeline, run_single_agent
from .errors import load_error_log, get_error_summary


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
        "--errors", action="store_true", help="Show error log from .cc/error_log.json"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw JSON (use with --errors)",
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("CC_PROVIDER", "claude"),
        help="LLM provider (claude, gpt4, gemini)",
    )
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    info = ensure_bootstrap()
    if args.check:
        print("[codecompanion] OK. Bootstrap dir:", info["dir"])
        if info["created"]:
            print("[codecompanion] Created:", ", ".join(info["created"]))
        print("[codecompanion] Agents dir:", info["agents_dir"])
        print("[codecompanion] Provider:", args.provider)
        return 0

    if args.errors:
        return show_errors(raw=args.raw)
    if args.chat:
        return chat_repl(provider=args.provider)
    if args.auto:
        return run_pipeline(provider=args.provider)
    if args.run:
        return run_single_agent(args.run, provider=args.provider)
    # default help
    parser.print_help()
    return 0


def show_errors(raw: bool = False):
    """Display error log in human-readable or JSON format."""
    import json

    records = load_error_log()

    if not records:
        print("\n✓ No errors recorded for this project.\n")
        return 0

    if raw:
        # Output raw JSON
        data = [
            {
                "timestamp": r.timestamp,
                "agent": r.agent,
                "stage": r.stage,
                "message": r.message,
                "severity": r.severity,
                "recovered": r.recovered,
                "details": r.details,
            }
            for r in records
        ]
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    # Human-readable format
    summary = get_error_summary()

    print("\nError Log (.cc/error_log.json)")
    print("=" * 60)
    print()

    for record in records:
        # Format timestamp (just time part)
        timestamp = record.timestamp.split("T")[0] + " " + record.timestamp.split("T")[1][:8]

        # Status symbol
        status = "✓" if record.recovered else "✗"

        # Severity indicator
        severity = "WARNING" if record.severity == "warning" else "ERROR  "

        print(f"[{timestamp}] {severity} | {record.agent} | {record.stage}")
        print(f"  {status} {'Recovered successfully' if record.recovered else 'Unrecovered failure'}")
        print(f"  Message: {record.message}")
        print()

    # Summary
    print("─" * 60)
    print(
        f"Total: {summary['total']} errors "
        f"({summary['unrecovered']} unrecovered, {summary['recovered']} recovered)"
    )
    print()

    if not raw:
        print("Tip: Run `codecompanion --errors --raw` for JSON output.")

    return 0
