# CodeCompanion – Multi-Model Dev OS Architecture (Vision v1)

## 1. Purpose

CodeCompanion is my internal "software studio in a box" designed to rapidly build Quillography suites and other micro-SaaS applications. It orchestrates multiple AI models (GPT, Claude, Gemini) as specialized agents to plan, architect, and generate implementation instructions for new features and projects.

The system is built to match my existing development workflow:

1. **Create a new GitHub repository** for the project
2. **Use Claude Code (web)** for scaffolding and implementing major features
3. **Pull to Replit**, where a single Run workflow executes `bash start-dev.sh`
4. **Use Claude Code (shell)** for smaller fixes, tests, and refinements

CodeCompanion doesn't replace this workflow—it enhances it by providing intelligent planning, architecture decisions, and clear implementation prompts that I can paste directly into Claude Code (web or shell).

## 2. Design Principles

CodeCompanion follows these core principles to ensure safe, efficient, and maintainable development:

- **Safety first**: Always create rollback checkpoints (git tags) before major changes
- **One focused task at a time**: Break work into discrete, manageable chunks
- **Full-file rewrites, not patch noise**: Generate complete, clean files rather than incremental patches
- **Multi-model by default**: Leverage GPT, Claude, and Gemini (minimum) to get diverse perspectives
- **Reusable patterns**: Maintain templates for common stacks (FastAPI, Flask, React, Next.js, etc.)
- **Fast feedback**: Run tests and basic checks after every major change

## 3. High-Level Architecture

### 3.1 Orchestrator (Project Manager Agent)

The Orchestrator is the central coordinator that manages project state and workflow:

- **Tracks project state**: Current phase, open tasks, completed milestones, checkpoint tags
- **Decides which agent to call next**: Routes work to the appropriate specialist based on project needs
- **Enforces workflow rules**:
  - Create checkpoint before big changes
  - Run tests after major modifications
  - Ensure plan and architecture exist before building features
  - Validate that prerequisites are met before advancing phases

The Orchestrator maintains awareness of the entire development lifecycle and ensures that safety measures and quality gates are consistently applied.

### 3.2 Planner Council (Multi-Model)

The Planner Council provides diverse strategic perspectives by consulting three AI models:

- **Planner-GPT**
- **Planner-Claude**
- **Planner-Gemini**

**Workflow:**

1. All three planners receive the project goal or feature request
2. Each returns an independent plan containing:
   - Phases and milestones
   - Task breakdown
   - Risk assessment
   - Technology recommendations
3. The Orchestrator merges the three plans into a unified strategy
4. Disagreements or alternative approaches are documented as "Open Questions" for human review

**Output files:**

- `ops/PLAN.md` – The merged project plan with phases, tasks, and open questions
- `TODO.json` – Structured task list with status tracking

This multi-model approach helps identify edge cases, alternative architectures, and potential issues that a single model might miss.

### 3.3 Architect Agent

The Architect takes the merged plan and transforms it into concrete technical specifications:

**Outputs:**

- `docs/ARCHITECTURE.md` – System overview, key modules, data flow, and component responsibilities
- `ops/PHASES.md` – Detailed breakdown of what gets built in each development phase

**Responsibilities:**

- Decide folder layout and project structure
- Choose technology stack and frameworks
- Define module boundaries and interfaces
- Establish data models and API contracts
- Identify shared components and utilities

The Architect ensures that implementation follows a coherent design rather than evolving organically without structure.

### 3.4 Specialist Builder Agents

Specialist agents generate focused implementation instructions for specific domains:

- **Backend Engineer**: API endpoints, database models, business logic
- **Frontend/UI Engineer**: Components, layouts, user interactions
- **Test & QA**: Test suites, validation scripts, quality checks
- **Docs & Launch**: README, API docs, deployment guides

**Important**: Specialists **never directly edit the repository**. Instead, they produce:

- **Claude Code (web) prompts** for scaffolding and major feature implementation
- **Claude Code (shell) prompts** for tests, small fixes, and refinements

These prompts are human-readable instructions that I paste into Claude Code, maintaining full control over what gets applied to the codebase.

### 3.5 Tooling & Memory Layer

CodeCompanion maintains persistent state and reusable knowledge:

**Per-project memory files:**

- `ops/PLAN.md` – Strategic roadmap and feature plan
- `ops/PROJECT_STATE.json` – Current phase, task status, checkpoint history
- `ops/PHASES.md` – Phase-by-phase implementation guide
- `TODO.json` – Structured task tracking
- `docs/ARCHITECTURE.md` – Technical architecture documentation

**Cross-project templates:**

- Located under `patterns/` directory
- Starter templates: `FASTAPI`, `Flask`, `React`, `Next.js`, `Streamlit`, etc.
- Include common configurations, folder structures, and boilerplate

**Future enhancements:**

- Analytics tracking: hours per feature, test coverage, deployment frequency
- Pattern library: successful solutions from completed projects
- Knowledge base: common issues and their resolutions

## 4. Standard Workflow

### 4.1 New Project Flow

The typical workflow for starting a new project from scratch:

1. **I create a new GitHub repository** for the project (e.g., `quillography-debate-arena`)

2. **Orchestrator runs "Project Kickoff"** and invokes the Planner Council
   - I provide the project goal (e.g., "Build a debate arena platform with real-time voting")
   - Planner-GPT, Planner-Claude, and Planner-Gemini each generate independent plans
   - Orchestrator merges them and identifies open questions

3. **Planner Council writes outputs**:
   - `ops/PLAN.md` – Unified project plan
   - `TODO.json` – Initial task breakdown

4. **Architect generates technical specs**:
   - `docs/ARCHITECTURE.md` – System design and module structure
   - `ops/PHASES.md` – Phase-by-phase implementation roadmap

5. **Specialist generates Phase 1 scaffold prompt**:
   - Backend Engineer creates a detailed Claude Code (web) prompt
   - Prompt includes: folder structure, initial files, configuration, dependencies

6. **I paste the prompt into Claude Code (web)** and review/apply the changes
   - Claude Code scaffolds the project structure
   - Creates initial files, configs, and boilerplate

7. **I pull the repository to Replit**:
   - The Run workflow executes `bash start-dev.sh`
   - Application starts up and is accessible for testing

8. **Repeat for subsequent features**:
   - Micro-plan: Specialist analyzes the next task
   - Generate prompt: Specialist creates implementation instructions
   - Apply: I paste into Claude Code and review changes
   - Test: Run tests and verify functionality
   - Checkpoint: Create git tag (e.g., `CHECKPOINT_USER_AUTH_COMPLETE`)

### 4.2 Existing Project Feature Flow

For adding features to an existing project with established architecture:

1. **Start from existing state**:
   - `ops/PLAN.md` and `docs/ARCHITECTURE.md` already exist
   - `ops/PROJECT_STATE.json` tracks current phase and completed work

2. **Request new feature**:
   - I describe the feature (e.g., "Add email notifications for new debates")
   - Orchestrator consults the existing plan and architecture

3. **Specialist creates focused plan**:
   - Reviews existing architecture to maintain consistency
   - Identifies affected modules and files
   - Notes any architectural impacts or new dependencies

4. **Generate implementation prompt**:
   - For major changes: Claude Code (web) prompt with full file contents
   - For minor changes: Claude Code (shell) prompt with targeted edits

5. **I apply changes via Claude Code**:
   - Paste prompt and review proposed changes
   - Apply to repository

6. **Test and validate**:
   - Run test suite: `pytest` or equivalent
   - Manually test the feature in Replit
   - Verify no regressions

7. **Create checkpoint**:
   - Git tag: `CHECKPOINT_EMAIL_NOTIFICATIONS_COMPLETE`
   - Update `ops/PROJECT_STATE.json` with completed task
   - Update `TODO.json` to mark task done

This workflow ensures that even as projects grow, new features are added systematically with proper planning, testing, and rollback points.

## 5. Roadmap

Future enhancements to expand CodeCompanion's capabilities:

- **Automatic git tag and commit message suggestions**: Orchestrator generates semantic commit messages and checkpoint tag names based on completed work

- **Visual dashboard showing project phases and tasks**: Web interface displaying project progress, phase completion, and task status in real-time

- **More specialized agents**:
  - **Security Auditor**: Scans for vulnerabilities, suggests security improvements
  - **Performance Tuner**: Analyzes bottlenecks, recommends optimizations
  - **Accessibility Specialist**: Ensures WCAG compliance for frontend components
  - **DevOps Engineer**: Manages CI/CD, deployment configurations, monitoring

- **Deeper Replit integration**:
  - Auto-generate `start-dev.sh` if missing based on detected framework
  - Suggest `.replit` configuration optimizations
  - Monitor Replit deployment status and health

- **Pattern learning and evolution**:
  - Extract successful patterns from completed projects
  - Evolve template library based on real-world usage
  - Build knowledge base of solutions to common challenges

- **Cross-project insights**:
  - Identify reusable components across Quillography suite
  - Track development velocity and predict timelines
  - Suggest code sharing opportunities between projects

- **Enhanced testing automation**:
  - Generate comprehensive test suites automatically
  - Suggest edge cases based on similar features in other projects
  - Run integration tests across multiple deployment environments

- **Documentation intelligence**:
  - Keep docs synchronized with code changes
  - Generate API documentation automatically from code
  - Create user guides and tutorials from feature descriptions

---

**Version**: 1.0
**Last Updated**: November 2025
**Status**: Living document – will evolve as CodeCompanion matures
