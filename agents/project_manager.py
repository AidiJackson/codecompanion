from typing import Dict, List, Any, Optional
import json
from .base_agent import BaseAgent

class ProjectManagerAgent(BaseAgent):
    """Project Manager Agent - Central orchestrator for project planning and coordination"""
    
    def __init__(self):
        super().__init__(
            name="Project Manager",
            role="Project Orchestrator",
            specialization="Project planning, requirements analysis, team coordination, and timeline management"
        )
        self.project_templates = {
            "Web Application": {
                "structure": ["frontend/", "backend/", "database/", "tests/"],
                "technologies": ["React/Vue", "Node.js/Python", "PostgreSQL/MongoDB"],
                "phases": ["Requirements", "Design", "Development", "Testing", "Deployment"]
            },
            "API Service": {
                "structure": ["src/", "tests/", "docs/", "config/"],
                "technologies": ["FastAPI/Express", "Database", "Authentication"],
                "phases": ["API Design", "Implementation", "Testing", "Documentation"]
            },
            "Data Pipeline": {
                "structure": ["data/", "processing/", "models/", "output/"],
                "technologies": ["Python", "Apache Airflow", "Data Storage"],
                "phases": ["Data Analysis", "Pipeline Design", "Implementation", "Monitoring"]
            }
        }
    
    def process_request(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process project management requests"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Project request: {request}\n\nCurrent context: {json.dumps(context, indent=2)}"}
        ]
        
        response_content = self.call_llm(messages)
        
        # Determine if we should hand off to specialists
        handoff_to = self.should_handoff(request, context)
        
        # Check if this is a new project request
        if any(keyword in request.lower() for keyword in ["new project", "create", "start", "build"]):
            # Generate project structure
            project_structure = self.generate_project_structure(request)
            response_content += f"\n\n📋 **Project Structure:**\n{project_structure}"
            handoff_to = "code_generator"  # Hand off to code generator for implementation
        
        # Check if we need UI/UX input
        elif any(keyword in request.lower() for keyword in ["interface", "design", "user experience", "frontend"]):
            handoff_to = "ui_designer"
        
        self.add_to_history(request, response_content)
        
        return {
            "content": response_content,
            "handoff_to": handoff_to,
            "agent": self.name,
            "files": self.generate_project_files(request) if "project" in request.lower() else None
        }
    
    def process_handoff(self, handoff_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process handoff from another agent"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Handoff from another agent: {handoff_content}\n\nProject context: {json.dumps(context, indent=2)}"}
        ]
        
        response_content = self.call_llm(messages, temperature=0.5)
        
        self.add_to_history(f"Handoff: {handoff_content}", response_content)
        
        return {
            "content": f"**Project Manager Update:**\n\n{response_content}",
            "agent": self.name
        }
    
    def generate_project_structure(self, request: str) -> str:
        """Generate a project structure based on the request"""
        # Simple project type detection
        if "web" in request.lower() or "app" in request.lower():
            template = self.project_templates["Web Application"]
        elif "api" in request.lower():
            template = self.project_templates["API Service"]
        elif "data" in request.lower():
            template = self.project_templates["Data Pipeline"]
        else:
            template = self.project_templates["Web Application"]  # Default
        
        structure = "```\n"
        for folder in template["structure"]:
            structure += f"📁 {folder}\n"
        structure += "```\n"
        
        structure += f"\n**Technologies:** {', '.join(template['technologies'])}\n"
        structure += f"**Development Phases:** {' → '.join(template['phases'])}"
        
        return structure
    
    def generate_project_files(self, request: str) -> Dict[str, str]:
        """Generate initial project files"""
        files = {}
        
        # Generate README.md
        files["README.md"] = f"""# Project Overview

## Description
{request}

## Project Structure
- Frontend: User interface and user experience
- Backend: Server-side logic and APIs
- Database: Data storage and management
- Tests: Quality assurance and validation

## Development Phases
1. **Requirements Analysis** - Define project scope and requirements
2. **System Design** - Architecture and component design
3. **Implementation** - Code development and integration
4. **Testing** - Quality assurance and bug fixes
5. **Deployment** - Production deployment and monitoring

## Getting Started
1. Review requirements and design documents
2. Set up development environment
3. Begin implementation following the project structure
4. Run tests to ensure quality
5. Deploy to production environment
"""
        
        # Generate project config
        files["project.json"] = json.dumps({
            "name": "Generated Project",
            "version": "1.0.0",
            "description": request,
            "created_by": "CodeCompanion Multi-Agent System",
            "agents_involved": ["project_manager"],
            "status": "initialized"
        }, indent=2)
        
        return files
    
    def get_system_prompt(self) -> str:
        """Get specialized system prompt for project manager"""
        base_prompt = super().get_system_prompt()
        return base_prompt + """
        
        As the Project Manager agent, you:
        - Analyze project requirements and create development plans
        - Break down complex projects into manageable tasks
        - Coordinate between different specialist agents
        - Ensure project timeline and scope management
        - Provide project status updates and recommendations
        
        When receiving requests:
        1. Analyze the project scope and complexity
        2. Create a structured development plan
        3. Identify which specialist agents should be involved
        4. Provide clear next steps and recommendations
        5. Hand off specific tasks to appropriate agents
        
        Always be comprehensive yet concise in your project planning.
        """
