# CodeCompanion CLI Usage Guide

The CodeCompanion CLI provides a powerful command-line interface to access the multi-agent AI system directly from your terminal.

## Installation & Setup

The CLI is already configured in this project. You can use it in two ways:

### Method 1: Direct wrapper script
```bash
./cc --help
```

### Method 2: Python module
```bash
python -m cc_cli.main --help
```

## Available Commands

### 1. Check Model Availability
Check which AI models have valid API keys configured:

```bash
./cc check
```

Example output:
```json
{
  "claude": true,
  "gpt4": true,
  "gemini": true
}
```

### 2. Run AI Pipeline
Execute the full multi-agent pipeline to generate complete project artifacts:

```bash
./cc run "Create a web scraper for news articles"
```

With custom output directory:
```bash
./cc run "Build a REST API with FastAPI" --outdir ./my-project
```

## Output Structure

When you run a project, the CLI generates the following files:

- **SPEC.md** - Project specification document (Claude)
- **PATCH.diff** - Code implementation patch (GPT-4)
- **DESIGN.md** - UI/UX design document (Gemini)
- **TESTPLAN.md** - Testing strategy (GPT-4)
- **EVAL.md** - Code review and evaluation (Claude)
- **manifest.json** - Complete run metadata

## Example Workflows

### Quick Prototype Generation
```bash
./cc run "Create a calculator app with GUI" --outdir ./calculator-prototype
```

### API Development
```bash
./cc run "Build a user authentication API with JWT tokens" --outdir ./auth-api
```

### Data Processing
```bash
./cc run "Create a CSV data analysis tool with visualization" --outdir ./data-tool
```

## Database Integration

All CLI runs are automatically saved to the project database for tracking and analysis. If database saving fails, the CLI will show a warning but continue to generate artifacts.

## Error Handling

- **Missing API Keys**: Commands will work with available models and skip unavailable ones
- **Network Issues**: API calls have built-in retry logic and timeout handling  
- **File System**: Output directories are created automatically
- **Database**: Failures are logged as warnings but don't stop execution

## Advanced Usage

### Environment Variables
Set API keys as environment variables:
```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
export GEMINI_API_KEY="your-key-here"
```

### Integration with Scripts
```bash
#!/bin/bash
# Generate multiple project variants
objectives=(
    "Create a blog platform"
    "Build a task management app" 
    "Design a file sharing system"
)

for obj in "${objectives[@]}"; do
    ./cc run "$obj" --outdir "./projects/$(echo "$obj" | tr ' ' '-')"
done
```

## Troubleshooting

### CLI not found
```bash
# Make sure the wrapper script is executable
chmod +x cc

# Or use the Python module directly
python -m cc_cli.main --help
```

### Import errors
```bash
# Ensure you're in the project root directory
pwd  # Should show your workspace path

# Check Python path includes current directory
python -c "import sys; print(sys.path)"
```

### API key issues
```bash
# Check which keys are available
./cc check

# Set missing keys in your environment
export OPENAI_API_KEY="sk-..."
```