import argparse
from .bootstrap import ensure_bootstrap
from . import __version__
from .runner import run_pipeline, run_single_agent
from .repl import chat_repl


def main():
    parser = argparse.ArgumentParser(
        prog="codecompanion", description="CodeCompanion AI Agent System"
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--check", action="store_true", help="Check installation")
    parser.add_argument("--auto", action="store_true", help="Run full agent pipeline")
    parser.add_argument("--run", metavar="AGENT", help="Run specific agent")
    parser.add_argument("--chat", action="store_true", help="Start chat REPL")
    parser.add_argument("--provider", default="claude", help="LLM provider")
    parser.add_argument("--detect", action="store_true", help="Detect project type")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    info = ensure_bootstrap()
    if args.check:
        print(f"[codecompanion] OK. Bootstrap dir: {info['dir']}")
        print(f"[codecompanion] Agents dir: {info['agents_dir']}")
        print(f"[codecompanion] Provider: {args.provider}")
        return 0

    if args.detect:
        from .detector import detect_and_configure

        detect_and_configure()
        return 0

    if args.chat:
        return chat_repl(args.provider)

    if args.auto:
        return run_pipeline(args.provider)

    if args.run:
        return run_single_agent(args.run, args.provider)

    # Show help
    parser.print_help()
    print("\n🤖 Available Agents:")
    print("  Installer, EnvDoctor, Analyzer, DepAuditor, BugTriage")
    print("  Fixer, TestRunner, WebDoctor, PRPreparer")
    return 0
