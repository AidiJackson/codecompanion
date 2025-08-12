import os
import json
from pathlib import Path

class ProjectDetector:
    """Detects project type and suggests optimal agent workflows"""
    
    FRAMEWORK_PATTERNS = {
        "react": ["package.json", "src/App.js", "src/App.tsx", "public/index.html"],
        "nextjs": ["package.json", "next.config.js", "pages/", "app/"],
        "vue": ["package.json", "src/App.vue", "vue.config.js"],
        "django": ["manage.py", "settings.py", "requirements.txt"],
        "flask": ["app.py", "application.py", "requirements.txt"],
        "fastapi": ["main.py", "requirements.txt", "uvicorn"],
        "streamlit": ["streamlit_app.py", "app.py", "requirements.txt"],
        "rust": ["Cargo.toml", "src/main.rs"],
        "go": ["go.mod", "main.go"],
        "rails": ["Gemfile", "config/application.rb"],
        "laravel": ["composer.json", "artisan", "app/Http/"],
    }
    
    AGENT_PRESETS = {
        "python-web": {
            "description": "Python web application (Django/Flask/FastAPI)",
            "agents": ["Installer", "EnvDoctor", "Analyzer", "DepAuditor", "WebDoctor", "TestRunner", "PRPreparer"],
            "focus": "Web framework setup, dependency management, testing"
        },
        "python-data": {
            "description": "Python data science/ML project",
            "agents": ["Installer", "EnvDoctor", "DepAuditor", "Analyzer", "TestRunner"],
            "focus": "Environment setup, package optimization, code analysis"
        },
        "node-frontend": {
            "description": "Node.js frontend application (React/Vue/Next)",
            "agents": ["Installer", "DepAuditor", "WebDoctor", "TestRunner", "BugTriage", "PRPreparer"],
            "focus": "NPM dependencies, build optimization, testing setup"
        },
        "node-backend": {
            "description": "Node.js backend API",
            "agents": ["Installer", "EnvDoctor", "Analyzer", "WebDoctor", "TestRunner", "PRPreparer"],
            "focus": "Server setup, API testing, security analysis"
        },
        "fullstack": {
            "description": "Full-stack application",
            "agents": ["Installer", "EnvDoctor", "Analyzer", "DepAuditor", "WebDoctor", "TestRunner", "BugTriage", "PRPreparer"],
            "focus": "Complete development workflow"
        },
        "generic": {
            "description": "Generic project",
            "agents": ["Installer", "EnvDoctor", "Analyzer", "TestRunner"],
            "focus": "Basic setup and analysis"
        }
    }

    @classmethod
    def detect_project_type(cls, project_path="."):
        """Detect project type and framework"""
        path = Path(project_path)
        detected = {
            "type": "generic",
            "framework": None,
            "language": None,
            "confidence": 0.0
        }
        
        # Check for specific frameworks
        for framework, patterns in cls.FRAMEWORK_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                if (path / pattern).exists():
                    matches += 1
            
            confidence = matches / len(patterns)
            if confidence > detected["confidence"]:
                detected["framework"] = framework
                detected["confidence"] = confidence
        
        # Determine language and type
        if (path / "package.json").exists():
            detected["language"] = "javascript"
            if detected["framework"] in ["react", "vue", "nextjs"]:
                detected["type"] = "node-frontend"
            else:
                detected["type"] = "node-backend"
        elif any((path / f).exists() for f in ["requirements.txt", "pyproject.toml", "setup.py"]):
            detected["language"] = "python"
            if detected["framework"] in ["django", "flask", "fastapi", "streamlit"]:
                detected["type"] = "python-web"
            else:
                detected["type"] = "python-data"
        elif (path / "Cargo.toml").exists():
            detected["language"] = "rust"
            detected["type"] = "rust"
        elif (path / "go.mod").exists():
            detected["language"] = "go"
            detected["type"] = "go"
        
        # Check for fullstack indicators
        has_frontend = any((path / f).exists() for f in ["package.json", "src/", "public/"])
        has_backend = any((path / f).exists() for f in ["requirements.txt", "main.py", "app.py", "server.py"])
        
        if has_frontend and has_backend:
            detected["type"] = "fullstack"
        
        return detected

    @classmethod
    def get_recommended_preset(cls, project_info):
        """Get recommended agent preset based on project detection"""
        project_type = project_info.get("type", "generic")
        return cls.AGENT_PRESETS.get(project_type, cls.AGENT_PRESETS["generic"])

    @classmethod
    def create_project_config(cls, project_path="."):
        """Create .codecompanion.json configuration"""
        detection = cls.detect_project_type(project_path)
        preset = cls.get_recommended_preset(detection)
        
        config = {
            "project": detection,
            "preset": preset,
            "custom_agents": [],
            "environment": {
                "python_version": None,
                "node_version": None,
                "required_packages": []
            },
            "created_at": None
        }
        
        config_path = Path(project_path) / ".codecompanion.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        return config

def detect_and_configure():
    """CLI function for project detection and configuration"""
    detector = ProjectDetector()
    project_info = detector.detect_project_type()
    preset = detector.get_recommended_preset(project_info)
    
    print(f"🔍 Project Detection Results:")
    print(f"  Type: {project_info['type']}")
    print(f"  Language: {project_info.get('language', 'unknown')}")
    print(f"  Framework: {project_info.get('framework', 'none')}")
    print(f"  Confidence: {project_info['confidence']:.0%}")
    print()
    print(f"📋 Recommended Preset: {preset['description']}")
    print(f"🎯 Focus: {preset['focus']}")
    print(f"🤖 Agents: {', '.join(preset['agents'])}")
    
    return project_info, preset

if __name__ == "__main__":
    detect_and_configure()