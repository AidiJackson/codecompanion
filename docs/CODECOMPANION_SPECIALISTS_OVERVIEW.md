# CodeCompanion Specialist Agents (Skeleton v1)

## Overview

CodeCompanion now includes a Specialist Agent system that allows targeted dispatch of development tasks to specialized agents. Each specialist focuses on a specific domain of software development and generates Claude Code-compatible prompts to guide implementation.

## Available Specialists

### Backend Specialist

**Focus Areas:**
- Server-side features and API design
- Data models and persistence layers
- Integration with external services
- Backend logic and business rules

**Files Modified:**
- Typically targets: `app/api`, `models/`, `schemas/`, backend service files

**Usage:**
```python
from codecompanion.orchestrator import Orchestrator

orchestrator = Orchestrator()
result = orchestrator.run_specialist(
    "backend",
    "Add user authentication endpoint with JWT tokens"
)
```

### Frontend Specialist

**Focus Areas:**
- UI/UX design and implementation
- Component architecture
- User interaction and state management
- Client-side logic

**Files Modified:**
- Typically targets: `src/pages`, `src/components`, UI asset files

**Usage:**
```python
result = orchestrator.run_specialist(
    "frontend",
    "Create responsive dashboard with user metrics"
)
```

### Test Specialist

**Focus Areas:**
- Test coverage and quality
- Generating or improving test cases
- Running pytest or relevant test commands
- Regression protection and edge case coverage

**Files Modified:**
- Typically targets: `tests/`, `test_*.py`, `*_test.py`

**Usage:**
```python
result = orchestrator.run_specialist(
    "test",
    "Add integration tests for authentication flow"
)
```

### Docs Specialist

**Focus Areas:**
- README files
- API documentation
- Internal developer documentation
- Documentation maintenance

**Files Modified:**
- Typically targets: `README.md`, `docs/*.md`, API documentation files

**Usage:**
```python
result = orchestrator.run_specialist(
    "docs",
    "Update API documentation for new authentication endpoints"
)
```

## Current Capabilities (v1 Skeleton)

### What It Does Today
- Generates structured Claude Code (web) prompts
- Provides domain-specific guidance and context
- Returns actionable steps for implementation
- Includes notes about assumptions and limitations

### What It Returns

Each specialist returns a `SpecialistResult` containing:
- **description**: Natural-language explanation of what the specialist will do
- **prompts**: List of Claude Code-compatible prompts to execute
- **notes**: Important assumptions, risks, or TODOs

Example:
```python
result = orchestrator.run_specialist("backend", "Add user API")
print(result.description)
# "Backend specialist stub. Prepares a Claude Code (web) prompt to implement..."

print(result.prompts[0])
# "You are Claude Code working on the backend of this project.\n\nGOAL\n..."

print(result.notes)
# ["This is a skeleton backend specialist; real implementations will..."]
```

## Future Enhancements

The v1 skeleton is intentionally limited. Future versions will include:

### Deep Repository Analysis
- Automatic detection of relevant files and patterns
- Understanding of existing code structure
- Smart suggestions for where to make changes

### Direct Code Changes
- Ability to modify files directly (not just generate prompts)
- Integrated quality gates and validation
- Automatic test execution after changes

### Quality Gates
- Pre-commit checks
- Code style validation
- Test coverage requirements
- Breaking change detection

### Enhanced Context
- Project history analysis
- Dependency graph understanding
- Cross-specialist coordination
- Task decomposition and planning

## Architecture

### Module Structure
```
codecompanion/
├── orchestrator.py          # Main orchestrator for dispatching
└── specialists/
    ├── __init__.py          # Module exports
    ├── base.py              # BaseSpecialist interface + SpecialistResult
    ├── backend.py           # BackendSpecialist implementation
    ├── frontend.py          # FrontendSpecialist implementation
    ├── test.py              # TestSpecialist implementation
    └── docs.py              # DocsSpecialist implementation
```

### Base Interface

All specialists implement `BaseSpecialist`:
```python
class BaseSpecialist:
    def run_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> SpecialistResult:
        raise NotImplementedError()
```

### Result Structure

```python
@dataclass
class SpecialistResult:
    description: str        # What this specialist focuses on
    prompts: List[str]      # Claude Code prompts to execute
    notes: List[str]        # Assumptions, risks, TODOs
```

## Integration

### Using with Orchestrator

```python
from codecompanion.orchestrator import Orchestrator

# Initialize orchestrator
orchestrator = Orchestrator()

# Dispatch to backend specialist
backend_result = orchestrator.run_specialist(
    specialist_name="backend",
    task="Implement user registration API",
    context={"priority": "high"}  # Optional context
)

# Use the generated prompts
for prompt in backend_result.prompts:
    # Send to Claude Code (web) or other execution engine
    execute_prompt(prompt)
```

### Error Handling

```python
try:
    result = orchestrator.run_specialist("unknown", "some task")
except ValueError as e:
    print(f"Unknown specialist: {e}")
```

## Notes

- This is a **structure-only** implementation
- No real LLM calls are made yet
- No code editing logic is implemented
- Focus is on clean types, docstrings, and extensibility
- The `context` parameter is reserved for future use

## Contributing

When extending specialists:
1. Follow the `BaseSpecialist` interface
2. Return structured `SpecialistResult` objects
3. Keep prompts generic with placeholders
4. Document assumptions in notes
5. Maintain consistent docstring format
