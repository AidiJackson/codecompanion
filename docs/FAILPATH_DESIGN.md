# Enterprise Fail-Path & Recovery Design

## Overview

This document describes the enterprise-grade fail-path, error-handling, and recovery layer for CodeCompanion's multi-agent workflow system.

## Goals

- **Zero-surprise behaviour**: Clear, predictable error handling
- **Strong protections**: Validate agent outputs to catch issues early
- **Clear error surfaces**: User-friendly error reporting in CLI
- **Safe state handling**: Maintain system integrity during failures
- **Future extensibility**: Hooks for LLM-driven self-repair

## Architecture

### Current Agent Workflow

CodeCompanion runs 9 agents sequentially:
1. **Installer** (tooling) - Environment setup, dependencies
2. **EnvDoctor** (claude) - Diagnose import/runtime issues
3. **Analyzer** (gpt4) - Code analysis, pattern detection
4. **DepAuditor** (gemini) - Dependency optimization
5. **BugTriage** (claude) - Bug reproduction, debugging
6. **Fixer** (gpt4) - Code generation, patches
7. **TestRunner** (tooling) - Test execution, coverage
8. **WebDoctor** (gemini) - Web app configuration
9. **PRPreparer** (claude) - Documentation, commits

### Fail-Path Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Execution Layer                     │
│  (runner.py: run_pipeline, run_single_agent)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Fail-Path Wrapper                          │
│  • Validates agent output                                    │
│  • Logs errors to .cc/error_log.json                        │
│  • Attempts recovery if validation fails                     │
│  • Returns enriched result (success, data, errors)           │
└─────────────────────────────────────────────────────────────┘
         │                    │                     │
         ▼                    ▼                     ▼
┌─────────────┐    ┌─────────────────┐    ┌────────────────┐
│ Validators  │    │ Error Logging   │    │ Recovery       │
│ Module      │    │ Module          │    │ Engine         │
└─────────────┘    └─────────────────┘    └────────────────┘
```

## Data Structures

### ValidationResult

```python
@dataclass
class ValidationResult:
    ok: bool                    # Validation passed?
    issues: list[str]           # List of validation issues
    agent: str                  # Agent name
    raw: Any                    # Raw agent output
    metadata: dict[str, Any]    # Additional context
```

### ErrorRecord

```python
@dataclass
class ErrorRecord:
    timestamp: str              # ISO timestamp
    agent: str                  # Agent name (e.g., "Analyzer")
    stage: str                  # Workflow stage
    message: str                # Human-readable error
    severity: str               # "warning" | "error"
    recovered: bool             # Was recovery successful?
    details: dict[str, Any]     # Additional error context
```

### RetryConfig

```python
@dataclass
class RetryConfig:
    max_attempts: int           # Maximum retry attempts
    backoff: float              # Backoff delay (seconds)
    fallback_enabled: bool      # Use fallback model?
```

### RecoveryResult

```python
@dataclass
class RecoveryResult:
    ok: bool                    # Recovery successful?
    attempts: int               # Number of attempts made
    used_fallback: bool         # Used fallback strategy?
    final_payload: Any          # Recovered output (if ok)
    error: str | None           # Error message (if not ok)
```

## Core Modules

### 1. validators.py

**Purpose**: Validate raw agent outputs for structural correctness

**Key Functions**:
- `validate_agent_output(agent: str, payload: Any) -> ValidationResult`
  - Validates based on agent-specific rules
  - Checks for non-empty output
  - Verifies expected structure (for LLM-based agents)
  - Does NOT raise exceptions - returns ValidationResult

**Validation Rules**:
- **All agents**: Output must be non-empty
- **LLM-based agents** (EnvDoctor, Analyzer, BugTriage, Fixer, PRPreparer, DepAuditor, WebDoctor):
  - If output is dict: Check for reasonable keys
  - If output is str: Check for minimum length, avoid pure error strings
  - Check for common LLM failure patterns (e.g., "I cannot", "Error:", etc.)
- **Tooling agents** (Installer, TestRunner):
  - Validate return codes (0 = success)
  - Check stdout/stderr if applicable

### 2. errors.py

**Purpose**: Centralized error logging and retrieval

**Key Functions**:
- `load_error_log(path: Path | str = ".cc/error_log.json") -> list[ErrorRecord]`
- `save_error_log(records: list[ErrorRecord], path=...) -> None`
- `append_error(record: ErrorRecord, path=...) -> None`

**Storage**:
- JSON file at `.cc/error_log.json`
- Each record is serialized as a dict
- File is created on first error (not pre-created)
- Supports concurrent access (basic file locking or append-only)

**ErrorSeverity Constants**:
- `WARNING = "warning"` - Non-critical issue, agent continued
- `ERROR = "error"` - Critical issue, agent failed

### 3. recovery.py

**Purpose**: Implement retry and recovery strategies

**Key Class**: `RecoveryEngine`

```python
class RecoveryEngine:
    def __init__(self, retry_config: RetryConfig):
        self.config = retry_config

    def attempt_recover(
        self,
        agent: str,
        raw_output: Any,
        issues: list[str]
    ) -> RecoveryResult:
        """
        Attempt to recover from validation failure.

        Current Strategy (Phase F):
        1. If issues empty → immediate success
        2. If raw_output is JSON string → try parsing
        3. If parsing succeeds → recovered
        4. Otherwise → unrecovered failure

        Future Strategy (Phase G+):
        - Use model_policy to select fallback LLM
        - Re-run agent with modified prompt
        - Apply LLM-driven self-repair
        """
```

## Integration Points

### Runner Integration (runner.py)

Modify `run_pipeline()` and `run_single_agent()` to:

1. Wrap agent execution with fail-path logic
2. Validate agent output after execution
3. Log errors to `.cc/error_log.json`
4. Attempt recovery if validation fails
5. Return enriched results

**New Helper Function**:
```python
def _run_with_failpath(
    agent_name: str,
    agent_fn: Callable,
    provider: str | None,
    config: RetryConfig
) -> tuple[int, dict]:
    """
    Execute agent with fail-path protection.

    Returns:
        (return_code, metadata)
        - return_code: 0 = success, 1 = unrecovered failure, 2 = recovered
        - metadata: {
            "agent": str,
            "success": bool,
            "recovered": bool,
            "errors": list[ErrorRecord],
            "output": Any
        }
    """
```

### CLI Integration (cli.py)

Add new command-line arguments:
- `--errors` - Show error log
- Enhance existing output with error context

New behavior:
- After `--auto` completes: Print error summary if any errors occurred
- After `--run <agent>`: Print agent-specific errors
- New `--errors` command: Pretty-print full error log

### Settings Integration

Create/update `.cc/settings.json` with:

```json
{
  "fail_path": {
    "max_attempts": 2,
    "backoff_seconds": 0.0,
    "fallback_enabled": false,
    "strict_validation": false
  },
  "version": "1.0.0"
}
```

Settings are:
- Created by `ensure_bootstrap()` if missing
- Loaded at CLI startup
- Passed to `_run_with_failpath()` as `RetryConfig`

## Error Reporting UX

### Success Case (No Errors)
```bash
$ codecompanion --auto
[agent] Installer (provider: none)
[installer] Setting up Python environment...
✓ Installer completed successfully

[agent] EnvDoctor (provider: claude)
[env-doctor] Diagnosing Python environment...
✓ EnvDoctor completed successfully

... (all agents succeed)

[ok] pipeline complete (9/9 agents succeeded)
```

### Failure with Recovery
```bash
$ codecompanion --auto
[agent] Analyzer (provider: gpt4)
[analyzer] Analyzing codebase structure...
⚠️  Analyzer output validation failed (attempting recovery...)
✓ Analyzer recovered successfully

... (pipeline continues)

[ok] pipeline complete (9/9 agents succeeded, 1 recovered)
Run `codecompanion --errors` to see details.
```

### Unrecovered Failure
```bash
$ codecompanion --auto
[agent] Fixer (provider: gpt4)
[fixer] Implementing fixes...
❌ Fixer failed validation and could not be recovered.

[error] Pipeline halted at agent: Fixer
Run `codecompanion --errors` for details.
```

### Errors Command
```bash
$ codecompanion --errors

Error Log (.cc/error_log.json)
════════════════════════════════════════════════════════════

[2025-11-18 12:30:45] ERROR | Analyzer | workflow.analyze
  ✗ Unrecovered failure
  Message: Output validation failed: Expected dict, got empty string

[2025-11-18 12:31:02] WARNING | Fixer | workflow.fix
  ✓ Recovered successfully
  Message: Output contained JSON parsing errors (recovered via retry)

Total: 2 errors (1 unrecovered, 1 recovered)

Run `codecompanion --errors --raw` for JSON output.
```

## Future Extensions

### Phase G: LLM-Driven Self-Repair

When recovery fails, use LLM to analyze and fix the issue:

```python
def _llm_self_repair(
    agent: str,
    raw_output: Any,
    issues: list[str],
    model_policy: ModelPolicy
) -> RecoveryResult:
    """
    Use LLM to analyze failure and generate corrected output.

    1. Select repair model via model_policy
    2. Construct repair prompt with:
       - Agent name and purpose
       - Raw output
       - Validation issues
    3. Ask LLM to fix or re-generate
    4. Re-validate result
    """
```

### Phase H: Multi-Model Fallback

When primary model fails, automatically fallback to alternative:

```python
# Example: Analyzer fails with GPT-4 → retry with Claude
fallback_map = {
    "gpt4": "claude",
    "claude": "gemini",
    "gemini": "gpt4"
}
```

### Phase I: Error Analytics

Aggregate error patterns for insights:
- Which agents fail most often?
- Which models are most reliable?
- Common validation issues?

## Backwards Compatibility

The fail-path layer is **fully backwards compatible**:

- Existing CLI commands work unchanged
- Agents that always succeed see no behavior change
- Error handling is opt-in (controlled by settings)
- Zero-config default (fail-fast, log errors, no retries)

## Implementation Checklist

- [ ] Create `codecompanion/validators.py`
- [ ] Create `codecompanion/errors.py`
- [ ] Create `codecompanion/recovery.py`
- [ ] Update `codecompanion/bootstrap.py` to create settings.json
- [ ] Modify `codecompanion/runner.py` with `_run_with_failpath()`
- [ ] Add `--errors` command to `codecompanion/cli.py`
- [ ] Update `.gitignore` to ignore `.cc/error_log.json`
- [ ] Write unit tests for validators, errors, recovery
- [ ] Integration test: full pipeline with synthetic failures
- [ ] Documentation update: CLI_USAGE.md

## File Structure

```
codecompanion/
├── validators.py          # NEW: Output validation
├── errors.py              # NEW: Error logging
├── recovery.py            # NEW: Recovery engine
├── runner.py              # MODIFIED: Add fail-path wrapper
├── cli.py                 # MODIFIED: Add --errors command
├── bootstrap.py           # MODIFIED: Create settings.json
└── ...

.cc/
├── error_log.json         # NEW: Runtime error log (gitignored)
├── settings.json          # NEW: Fail-path configuration
├── agent_pack.json        # Existing
└── agents/                # Existing
```

## Testing Strategy

1. **Unit Tests**:
   - `test_validators.py`: Test each validation rule
   - `test_errors.py`: Test error logging I/O
   - `test_recovery.py`: Test recovery strategies

2. **Integration Tests**:
   - Run pipeline with mock agent that returns invalid output
   - Verify error is logged
   - Verify recovery attempt
   - Verify CLI error reporting

3. **Manual Testing**:
   - Run `codecompanion --auto` on real project
   - Verify clean execution (no spurious errors)
   - Inject failure by modifying agent output
   - Verify error log and recovery behavior

## Success Criteria

- ✅ All Python files pass `python -m compileall codecompanion`
- ✅ Existing happy-path remains unchanged
- ✅ CLI backwards compatible
- ✅ Error log created on first failure
- ✅ `codecompanion --errors` displays readable output
- ✅ Recovery engine runs (even if no-op currently)
- ✅ Settings.json created by bootstrap
- ✅ `.gitignore` updated for runtime artifacts
- ✅ Full pipeline runs successfully end-to-end

---

**Document Version**: 1.0
**Date**: 2025-11-18
**Status**: Implementation Ready
