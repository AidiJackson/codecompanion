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

### 3. Git Push Integration
Initialize git repository, commit artifacts, and optionally push to remote:

```bash
./cc git-push ./my-project
```

With custom commit message:
```bash
./cc git-push ./my-project --message "Initial implementation from CodeCompanion"
```

With GitHub repository (requires GITHUB_TOKEN environment variable):
```bash
./cc git-push ./my-project --repo-url "https://github.com/username/my-project.git" --message "Deploy from CodeCompanion"
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
./cc git-push ./calculator-prototype --message "Calculator prototype v1"
```

### API Development with Repository Publishing
```bash
./cc run "Build a user authentication API with JWT tokens" --outdir ./auth-api
export GITHUB_TOKEN="ghp_your_token_here"
./cc git-push ./auth-api --repo-url "https://github.com/username/auth-api.git" --message "Initial auth API implementation"
```

### Data Processing Pipeline
```bash
./cc run "Create a CSV data analysis tool with visualization" --outdir ./data-tool
./cc git-push ./data-tool --message "Data analysis tool with charts"
```

### Complete Development Workflow
```bash
# Generate project
./cc run "Build a blog platform with admin panel" --outdir ./blog-platform

# Review generated artifacts
ls -la ./blog-platform/

# Initialize git and push to repository
export GITHUB_TOKEN="your_github_token"
./cc git-push ./blog-platform \
    --repo-url "https://github.com/username/blog-platform.git" \
    --message "Blog platform initial implementation from CodeCompanion"
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