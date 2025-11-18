"""
Project Scaffolder for CodeCompanion.
Creates new project workspaces with backend and frontend skeletons.
"""
import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict


@dataclass
class ProjectSpec:
    """Specification for a project to scaffold."""
    name: str
    slug: str
    summary: str
    frontend: str  # e.g., "vite-react"
    backend: str   # e.g., "fastapi"


def scaffold_project(spec: ProjectSpec) -> Dict:
    """
    Create a new project workspace with backend and frontend skeletons.

    Args:
        spec: ProjectSpec describing the project to create

    Returns:
        dict: Summary of what was created (paths, notes)
    """
    # Determine project directory
    project_root = Path.cwd()
    workspaces_dir = project_root / "workspaces"
    project_dir = workspaces_dir / spec.slug

    # Create directory structure
    backend_dir = project_dir / "backend"
    frontend_dir = project_dir / "frontend"

    paths_created = []

    # Create directories
    for d in [workspaces_dir, project_dir, backend_dir, frontend_dir]:
        if not d.exists():
            d.mkdir(parents=True)
            paths_created.append(str(d))

    # Write workspace.json metadata
    workspace_metadata = {
        **asdict(spec),
        "created_at": datetime.now().isoformat(),
        "workspaces_version": "1.0"
    }
    workspace_json_path = project_dir / "workspace.json"
    with open(workspace_json_path, "w") as f:
        json.dump(workspace_metadata, f, indent=2)
    paths_created.append(str(workspace_json_path))

    # Create backend skeleton (FastAPI)
    if spec.backend == "fastapi":
        _create_fastapi_backend(backend_dir, spec.name)
        paths_created.append(str(backend_dir / "main.py"))
        paths_created.append(str(backend_dir / "requirements.txt"))

    # Create frontend skeleton (Vite + React)
    if spec.frontend == "vite-react":
        _create_vite_react_frontend(frontend_dir, spec.name)
        paths_created.append(str(frontend_dir / "index.html"))
        paths_created.append(str(frontend_dir / "package.json"))
        paths_created.append(str(frontend_dir / "src" / "App.jsx"))

    # Create README
    readme_content = _generate_readme(spec)
    readme_path = project_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)
    paths_created.append(str(readme_path))

    return {
        "status": "success",
        "project_slug": spec.slug,
        "project_name": spec.name,
        "project_dir": str(project_dir),
        "paths_created": paths_created,
        "notes": f"Project '{spec.name}' scaffolded successfully at {project_dir}"
    }


def _create_fastapi_backend(backend_dir: Path, project_name: str):
    """Create a simple FastAPI backend with a health endpoint."""
    # main.py
    main_py_content = f'''"""
{project_name} - FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{project_name}")

# CORS setup for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy", "service": "{project_name}"}}


@app.get("/")
async def root():
    """Root endpoint."""
    return {{"message": "Welcome to {project_name} API"}}
'''

    main_py_path = backend_dir / "main.py"
    with open(main_py_path, "w") as f:
        f.write(main_py_content)

    # requirements.txt
    requirements_content = """fastapi==0.104.1
uvicorn[standard]==0.24.0
"""
    requirements_path = backend_dir / "requirements.txt"
    with open(requirements_path, "w") as f:
        f.write(requirements_content)


def _create_vite_react_frontend(frontend_dir: Path, project_name: str):
    """Create a simple Vite + React frontend."""
    src_dir = frontend_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # index.html
    index_html_content = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''
    with open(frontend_dir / "index.html", "w") as f:
        f.write(index_html_content)

    # package.json
    package_json_content = f'''{{
  "name": "{project_name.lower().replace(' ', '-')}",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }},
  "devDependencies": {{
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }}
}}
'''
    with open(frontend_dir / "package.json", "w") as f:
        f.write(package_json_content)

    # vite.config.js
    vite_config_content = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  }
})
'''
    with open(frontend_dir / "vite.config.js", "w") as f:
        f.write(vite_config_content)

    # src/main.jsx
    main_jsx_content = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
'''
    with open(src_dir / "main.jsx", "w") as f:
        f.write(main_jsx_content)

    # src/App.jsx
    app_jsx_content = f'''import {{ useState }} from 'react'

function App() {{
  return (
    <div style={{{{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#0f172a',
      color: '#e2e8f0',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}}}>
      <h1 style={{{{ fontSize: '3rem', marginBottom: '1rem' }}}}>
        {project_name}
      </h1>
      <p style={{{{ color: '#94a3b8', fontSize: '1.2rem' }}}}>
        Your project is ready!
      </p>
    </div>
  )
}}

export default App
'''
    with open(src_dir / "App.jsx", "w") as f:
        f.write(app_jsx_content)

    # src/index.css
    index_css_content = '''* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
'''
    with open(src_dir / "index.css", "w") as f:
        f.write(index_css_content)


def _generate_readme(spec: ProjectSpec) -> str:
    """Generate README.md content for the project."""
    return f"""# {spec.name}

{spec.summary}

## Stack

- **Backend**: {spec.backend}
- **Frontend**: {spec.frontend}

## Getting Started

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`

- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Project Structure

```
{spec.slug}/
├── backend/          # FastAPI backend
│   ├── main.py
│   └── requirements.txt
├── frontend/         # Vite + React frontend
│   ├── src/
│   ├── index.html
│   └── package.json
├── workspace.json    # Project metadata
└── README.md         # This file
```

## Development

- Backend runs on port 8000
- Frontend runs on port 5173
- CORS is configured for local development

---

Generated by CodeCompanion Project Scaffolder
"""


def scaffold_crossword_demo() -> Dict:
    """
    Create a demo 'crossword-arcade' project with:
    - FastAPI backend with puzzle API placeholder
    - Vite+React frontend with a 5x5 grid display
    """
    spec = ProjectSpec(
        name="Crossword Arcade",
        slug="crossword-arcade",
        summary="A demo crossword puzzle game with daily puzzles",
        frontend="vite-react",
        backend="fastapi"
    )

    # Scaffold base project
    result = scaffold_project(spec)

    # Enhance backend with crossword-specific routes
    project_dir = Path.cwd() / "workspaces" / spec.slug
    backend_dir = project_dir / "backend"

    # Overwrite main.py with crossword-specific version
    crossword_main_py = '''"""
Crossword Arcade - FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Crossword Arcade")

# CORS setup for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Crossword Arcade"}


@app.get("/api/daily-puzzle")
async def get_daily_puzzle():
    """
    Get today's crossword puzzle.
    Returns a simple 5x5 grid placeholder.
    """
    return {
        "id": "demo-001",
        "date": "2025-01-15",
        "size": {"rows": 5, "cols": 5},
        "grid": [
            ["C", "R", "O", "S", "S"],
            ["O", "", "", "", ""],
            ["D", "", "", "", ""],
            ["E", "", "", "", ""],
            ["R", "", "", "", ""]
        ],
        "clues": {
            "across": [
                {"number": 1, "clue": "Word game with grids", "answer": "CROSS"}
            ],
            "down": [
                {"number": 1, "clue": "Someone who writes programs", "answer": "CODER"}
            ]
        }
    }
'''

    with open(backend_dir / "main.py", "w") as f:
        f.write(crossword_main_py)

    # Enhance frontend with crossword grid
    frontend_dir = project_dir / "frontend"
    src_dir = frontend_dir / "src"

    crossword_app_jsx = '''import { useState, useEffect } from 'react'

function App() {
  const [puzzle, setPuzzle] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('http://localhost:8000/api/daily-puzzle')
      .then(res => res.json())
      .then(data => {
        setPuzzle(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load puzzle:', err)
        setLoading(false)
      })
  }, [])

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#0f172a',
      color: '#e2e8f0',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      padding: '2rem'
    }}>
      <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>
        🎯 Crossword Arcade
      </h1>

      {loading && <p>Loading puzzle...</p>}

      {!loading && puzzle && (
        <div style={{ marginTop: '2rem' }}>
          <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>
            Daily Puzzle #{puzzle.id} - {puzzle.date}
          </p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${puzzle.size.cols}, 60px)`,
            gap: '2px',
            backgroundColor: '#1e293b',
            padding: '2px',
            borderRadius: '8px'
          }}>
            {puzzle.grid.flat().map((letter, idx) => (
              <div
                key={idx}
                style={{
                  width: '60px',
                  height: '60px',
                  backgroundColor: letter ? '#e2e8f0' : '#0f172a',
                  color: '#0f172a',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.5rem',
                  fontWeight: 'bold',
                  border: '1px solid #475569'
                }}
              >
                {letter}
              </div>
            ))}
          </div>

          <div style={{ marginTop: '2rem', maxWidth: '400px' }}>
            <h3 style={{ marginBottom: '0.5rem' }}>Clues:</h3>
            <div style={{ color: '#94a3b8' }}>
              <p><strong>Across:</strong></p>
              {puzzle.clues.across.map(clue => (
                <p key={clue.number}>
                  {clue.number}. {clue.clue}
                </p>
              ))}
              <p style={{ marginTop: '0.5rem' }}><strong>Down:</strong></p>
              {puzzle.clues.down.map(clue => (
                <p key={clue.number}>
                  {clue.number}. {clue.clue}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      {!loading && !puzzle && (
        <p style={{ color: '#ef4444' }}>
          Failed to load puzzle. Make sure the backend is running on port 8000.
        </p>
      )}
    </div>
  )
}

export default App
'''

    with open(src_dir / "App.jsx", "w") as f:
        f.write(crossword_app_jsx)

    result["notes"] = "Crossword Arcade demo scaffolded with 5x5 grid and daily puzzle API"
    return result
