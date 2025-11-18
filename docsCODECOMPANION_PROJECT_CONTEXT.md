📦 CODECOMPANION PROJECT CONTEXT PACK — v2
(Updated 18 Nov 2025 — CLI + Settings Integrated)

🔵 Project: CodeCompanion
An AI-powered, multi-LLM development operating system built for ultra-fast software creation, orchestration, planning, and code execution.

This context pack ensures ALL future chats (ChatGPT, Claude, Gemini) can resume instantly with full project awareness.

🟣 1. Current Active Branch
claude/specialist-agents-skeleton-015EsQLBrfMNny8Q9wE4h4bG-018PgJgrZxeSW3W2W5N5Gs1K
All commits since the CLI phase have been pushed here.
This is the only branch to be used for now.

🔵 2. Core Architectural Components (Implemented So Far)
✅ 2.1 Planner Council (3-Model Design)
Planner_GPT

Planner_Claude

Planner_Gemini

Orchestrator merges their plans into a merged_plan JSON object.

Merged plan is passed to Architect + Specialists.

(Code exists in previous branches — full integration coming later.)

✅ 2.2 Architect Agent Skeleton
Located in:

codecompanion/architect/
ArchitectAgent consumes the merged plan

Generates two documents:

/docs/ARCHITECTURE.md

/ops/PHASES.md

Orchestrator tracks architecture_version and state in .codecompanion_state.json.

✅ 2.3 Specialist Agents Skeleton
Located in:

codecompanion/specialists/
Includes:

BackendSpecialist

FrontendSpecialist

TestSpecialist

DocsSpecialist

BaseSpecialist (shared interface)

Loader:

codecompanion/specialist_loader.py
Specialists accept tasks and produce structured results.

🟩 2.4 CLI System (NEW in v2)
Command entrypoint:
python -m codecompanion.cli <command>
Implemented subcommands:
✔ init
Creates:

.codecompanion_state.json

.codecompanion_settings.json

Outputs:

CodeCompanion project initialised.
State file: <path>
Settings file: <path>
✔ state
Prints:

project state

settings

combined JSON

raw mode via --raw

✔ run architect
Hooks into orchestrator (stub functional, full behaviour coming in later phases).

✔ run specialist --type TYPE
Loads correct specialist & executes skeleton run.

✔ quality
Hooks into quality gates module (stubs; will expand).

🟧 2.5 Configuration System (NEW in v2)
Settings file:
.codecompanion_settings.json

Default settings template:
{
  "project_name": "<directory>",
  "model_policy_mode": "balanced",
  "project_root": ".",
  "notes": []
}
Environment overrides:
CC_PROJECT_NAME

CC_MODEL_POLICY_MODE

Module:
codecompanion/settings.py
Integration:
Orchestrator loads settings on startup.

CLI depends on settings for project identity & behaviour.

🟥 2.6 State Management
State is stored in:

.codecompanion_state.json
Tracks:

initialized flag

version

architecture_version

specialists run

quality reports

auto_save flag

State reading is unified via Orchestrator.

🟩 2.7 Quality Gate Skeleton
Implemented:

codecompanion/quality_gates.py
Will be expanded into:

Lint gate

Security gate

Complexity gate

LLM-based code review gate

🟣 3. Development Workflow Rules
✔ All large work is done via Claude Code (web)
✔ All medium/small fixes via Claude Code (shell)
✔ User should never run git commands manually again
✔ Claude Code must:
NEVER switch branches

NEVER create branches

ALWAYS confirm branch before committing

ALWAYS push to the same branch

ALWAYS include commit hash

✔ Replit shell is used ONLY to:
read output

run python -m codecompanion.cli ... if needed

🔵 4. System Capabilities (Completed vs Pending)
✔ Completed
Base multi-agent architecture

Architect agent ready

Specialist agent skeletons

Settings/config system

CLI with init/state

CI safely removed across repo

Project root detection stub

State + settings persistence

CLI entrypoint (__main__) added

All modules compile cleanly

🔜 Pending (Next Phases)
Fully connect run architect → real doc generation

Fully connect specialists → produce actual diffs/patches

Add cc run planner (3-model planning pipeline)

Add model selection layer using MODEL_POLICY.json

Add Live Context + Memory snapshotting

Add project template generator

Create packageable install (pip install -e .)

End-to-end testing suite

Local code editing / patch application

Quillography.ai integration hooks

Error elimination layer (retry, validation, self-heal)

Zero-bug code style system (Lint → Format → Enforce)

🟦 5. How to Resume Work in a New Chat
Start any new chat with:

Load the CodeCompanion Project Context Pack v2 below as system context and continue development.
Paste this entire file underneath it.

You're instantly back where you left off.

🔥 6. Next Recommended Task (After Loading v2)
We proceed to the Happy Path Pipeline:

cc init
cc run architect
cc run specialist --type frontend
cc quality
cc state
We will implement the actual logic for:

architect generation

specialist execution

quality gates

orchestrator supervision

This turns CodeCompanion into a real "mini-developer".

🟩 7. End of Context Pack v2
Copy all of this into your repo file to make v2 official.

