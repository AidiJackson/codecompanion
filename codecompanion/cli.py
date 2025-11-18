import os
import argparse
import json
from .bootstrap import ensure_bootstrap
from . import __version__
from .repl import chat_repl
from .runner import run_pipeline, run_single_agent
from .settings import init_settings, load_settings
from .model_policy import load_model_policy
from .orchestrator import Orchestrator


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
    parser.add_argument("--init", action="store_true", help="Initialize settings")
    parser.add_argument("--state", action="store_true", help="Show current state and settings")
    parser.add_argument("--errors", action="store_true", help="Show error log")
    parser.add_argument("--policy", action="store_true", help="Show model policy")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    info = ensure_bootstrap()

    if args.init:
        settings = init_settings()
        print("[codecompanion] Settings initialized at .codecompanion_settings.json")
        print(json.dumps(settings.to_dict(), indent=2))
        return 0

    if args.state:
        settings = load_settings()
        print("[codecompanion] CURRENT STATE")
        print("\nSETTINGS:")
        print(json.dumps(settings.to_dict(), indent=2))
        print("\nBOOTSTRAP:")
        print(f"  Bootstrap dir: {info['dir']}")
        print(f"  Agents dir: {info['agents_dir']}")
        return 0

    if args.errors:
        orchestrator = Orchestrator()
        errors = orchestrator.get_error_summary(limit=20)
        if not errors:
            print("[codecompanion] No errors logged")
        else:
            print(f"[codecompanion] ERROR LOG ({len(errors)} recent errors)")
            for i, err in enumerate(errors, 1):
                print(f"\n{i}. {err.get('agent', 'unknown')} @ {err.get('stage', 'unknown')}")
                print(f"   Time: {err.get('timestamp', 'unknown')}")
                print(f"   Type: {err.get('error_type', 'unknown')}")
                print(f"   Message: {err.get('message', 'unknown')}")
                if err.get('recovered'):
                    print(f"   Status: RECOVERED (fallback: {err.get('used_fallback', False)})")
                    if err.get('details', {}).get('recovery_model'):
                        print(f"   Recovery model: {err['details']['recovery_model']}")
                else:
                    print(f"   Status: FAILED")
        return 0

    if args.policy:
        policy = load_model_policy()
        print("[codecompanion] MODEL POLICY")
        print(json.dumps(policy.to_dict(), indent=2))
        return 0

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
