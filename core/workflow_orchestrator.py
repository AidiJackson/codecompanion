from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import uuid

from core.model_orchestrator import AgentType


class ProjectComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ProjectType(Enum):
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    API_SERVICE = "api_service"
    DESKTOP_APP = "desktop_app"
    DATA_PIPELINE = "data_pipeline"
    MACHINE_LEARNING = "machine_learning"


class AgentStatus(Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    WORKING = "working"
    COLLABORATING = "collaborating"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


class WorkflowStep:
    def __init__(
        self, agent_type: AgentType, task: str, dependencies: Optional[List[str]] = None
    ):
        self.id = str(uuid.uuid4())[:8]
        self.agent_type = agent_type
        self.task = task
        self.dependencies = dependencies or []
        self.status = AgentStatus.IDLE
        self.progress = 0
        self.output: Optional[str] = None
        self.files_generated: Dict[str, str] = {}
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None


class WorkflowOrchestrator:
    """Advanced orchestration engine for coordinating multi-agent AI collaboration"""

    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.current_project = None
        self.workflow_steps = []
        self.agent_communications = []
        self.project_outputs = {
            "architecture": None,
            "code_files": {},
            "ui_designs": {},
            "test_suites": {},
            "debug_reports": {},
        }
        self.collaboration_log = []

    def analyze_project_requirements(
        self, description: str, project_type: ProjectType, complexity: ProjectComplexity
    ) -> Dict[str, Any]:
        """Analyze project requirements and determine optimal workflow"""

        # Define complexity-based agent requirements
        complexity_requirements = {
            ProjectComplexity.SIMPLE: {
                "required_agents": [
                    AgentType.PROJECT_MANAGER,
                    AgentType.CODE_GENERATOR,
                ],
                "optional_agents": [AgentType.UI_DESIGNER],
                "estimated_duration": "15-30 minutes",
                "phases": ["Planning", "Development", "Basic Testing"],
            },
            ProjectComplexity.MEDIUM: {
                "required_agents": [
                    AgentType.PROJECT_MANAGER,
                    AgentType.CODE_GENERATOR,
                    AgentType.UI_DESIGNER,
                    AgentType.TEST_WRITER,
                ],
                "optional_agents": [AgentType.DEBUGGER],
                "estimated_duration": "45-60 minutes",
                "phases": [
                    "Planning",
                    "Architecture",
                    "Development",
                    "Design",
                    "Testing",
                ],
            },
            ProjectComplexity.COMPLEX: {
                "required_agents": [
                    AgentType.PROJECT_MANAGER,
                    AgentType.CODE_GENERATOR,
                    AgentType.UI_DESIGNER,
                    AgentType.TEST_WRITER,
                    AgentType.DEBUGGER,
                ],
                "optional_agents": [],
                "estimated_duration": "1-2 hours",
                "phases": [
                    "Planning",
                    "Architecture",
                    "Development",
                    "Design",
                    "Testing",
                    "Optimization",
                    "Documentation",
                ],
            },
        }

        # Project type specific considerations
        type_requirements = {
            ProjectType.WEB_APP: {
                "technologies": [
                    "Frontend Framework",
                    "Backend API",
                    "Database",
                    "Authentication",
                ],
                "focus_areas": [
                    "User Experience",
                    "Responsive Design",
                    "Performance",
                    "Security",
                ],
            },
            ProjectType.MOBILE_APP: {
                "technologies": [
                    "Mobile Framework",
                    "API Integration",
                    "Local Storage",
                    "Push Notifications",
                ],
                "focus_areas": [
                    "Mobile UX",
                    "Performance",
                    "Offline Support",
                    "Platform Compatibility",
                ],
            },
            ProjectType.API_SERVICE: {
                "technologies": [
                    "API Framework",
                    "Database",
                    "Authentication",
                    "Documentation",
                ],
                "focus_areas": [
                    "Scalability",
                    "Security",
                    "Documentation",
                    "Error Handling",
                ],
            },
            ProjectType.DESKTOP_APP: {
                "technologies": [
                    "Desktop Framework",
                    "Local Database",
                    "File System",
                    "System Integration",
                ],
                "focus_areas": [
                    "User Interface",
                    "Performance",
                    "Cross-platform",
                    "Installation",
                ],
            },
        }

        requirements = complexity_requirements[complexity]
        type_info = type_requirements.get(project_type, {})

        analysis = {
            "project_id": str(uuid.uuid4())[:12],
            "description": description,
            "project_type": project_type.value,
            "complexity": complexity.value,
            "required_agents": requirements["required_agents"],
            "optional_agents": requirements["optional_agents"],
            "estimated_duration": requirements["estimated_duration"],
            "phases": requirements["phases"],
            "technologies": type_info.get("technologies", []),
            "focus_areas": type_info.get("focus_areas", []),
            "created_at": datetime.now().isoformat(),
        }

        return analysis

    def create_intelligent_workflow(
        self, project_analysis: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Create an intelligent workflow based on project analysis"""

        workflow_steps = []
        ProjectComplexity(project_analysis["complexity"])
        ProjectType(project_analysis["project_type"])

        # Phase 1: Project Planning (Project Manager)
        planning_step = WorkflowStep(
            agent_type=AgentType.PROJECT_MANAGER,
            task=f"Analyze requirements and create project architecture for {project_analysis['description']}",
        )
        workflow_steps.append(planning_step)

        # Phase 2: Backend Development (Code Generator)
        if AgentType.CODE_GENERATOR in project_analysis["required_agents"]:
            backend_step = WorkflowStep(
                agent_type=AgentType.CODE_GENERATOR,
                task="Implement core backend logic, APIs, and database models",
                dependencies=[planning_step.id],
            )
            workflow_steps.append(backend_step)

        # Phase 3: UI/UX Design (UI Designer)
        if AgentType.UI_DESIGNER in project_analysis["required_agents"]:
            ui_step = WorkflowStep(
                agent_type=AgentType.UI_DESIGNER,
                task="Create user interface designs and frontend components",
                dependencies=[planning_step.id],
            )
            workflow_steps.append(ui_step)

        # Phase 4: Testing (Test Writer)
        if AgentType.TEST_WRITER in project_analysis["required_agents"]:
            test_dependencies = [
                step.id
                for step in workflow_steps
                if step.agent_type in [AgentType.CODE_GENERATOR, AgentType.UI_DESIGNER]
            ]
            test_step = WorkflowStep(
                agent_type=AgentType.TEST_WRITER,
                task="Generate comprehensive test suites for all components",
                dependencies=test_dependencies,
            )
            workflow_steps.append(test_step)

        # Phase 5: Debugging & Optimization (Debugger)
        if AgentType.DEBUGGER in project_analysis["required_agents"]:
            debug_dependencies = [step.id for step in workflow_steps]
            debug_step = WorkflowStep(
                agent_type=AgentType.DEBUGGER,
                task="Analyze code quality, identify issues, and optimize performance",
                dependencies=debug_dependencies,
            )
            workflow_steps.append(debug_step)

        return workflow_steps

    def execute_workflow_step(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step with the appropriate AI model"""

        step.status = AgentStatus.WORKING
        step.started_at = datetime.now()
        step.progress = 10

        # Get the appropriate agent
        agent_mapping = {
            AgentType.PROJECT_MANAGER: "project_manager",
            AgentType.CODE_GENERATOR: "code_generator",
            AgentType.UI_DESIGNER: "ui_designer",
            AgentType.TEST_WRITER: "test_writer",
            AgentType.DEBUGGER: "debugger",
        }

        agent_key = agent_mapping.get(step.agent_type, "")
        agent = self.agents.get(agent_key)

        if not agent:
            step.status = AgentStatus.ERROR
            return {"error": f"Agent {agent_key} not available"}

        # Create enhanced context with project information
        enhanced_context = {
            **context,
            "workflow_step": {
                "id": step.id,
                "task": step.task,
                "agent_type": step.agent_type.value,
                "dependencies_completed": True,  # Simplified for now
            },
            "project_context": self.current_project,
        }

        try:
            # Simulate progress updates
            step.progress = 30

            # Execute the agent task
            result = agent.process_request(step.task, enhanced_context)

            step.progress = 80

            # Process the result
            step.output = result.get("content", "")
            step.files_generated = result.get("files", {})
            step.progress = 100
            step.status = AgentStatus.COMPLETED
            step.completed_at = datetime.now()

            # Log the collaboration
            self.collaboration_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "agent": step.agent_type.value,
                    "action": "completed_task",
                    "task": step.task,
                    "output_summary": step.output[:200] + "..."
                    if len(step.output) > 200
                    else step.output,
                }
            )

            return result

        except Exception as e:
            step.status = AgentStatus.ERROR
            step.progress = 0
            return {"error": str(e)}

    def orchestrate_project(
        self,
        project_description: str,
        project_type: ProjectType,
        complexity: ProjectComplexity,
    ) -> Dict[str, Any]:
        """Main orchestration method - coordinates entire multi-agent workflow"""

        # Phase 1: Analyze requirements
        self.current_project = self.analyze_project_requirements(
            project_description, project_type, complexity
        )

        # Phase 2: Create workflow
        self.workflow_steps = self.create_intelligent_workflow(self.current_project)

        # Phase 3: Execute workflow with intelligent coordination
        execution_context = {
            "project_analysis": self.current_project,
            "collaboration_history": [],
        }

        completed_steps = []

        # Continue processing until all steps are completed
        max_iterations = len(self.workflow_steps) * 2  # Prevent infinite loops
        iteration = 0

        while (
            len(completed_steps) < len(self.workflow_steps)
            and iteration < max_iterations
        ):
            iteration += 1
            steps_executed_this_round = 0

            for step in self.workflow_steps:
                # Skip if already completed
                if step in completed_steps:
                    continue

                # Check dependencies
                if self.are_dependencies_satisfied(step, completed_steps):
                    # Add collaboration communication
                    self.add_agent_communication(
                        f"{step.agent_type.value} is now working on: {step.task}"
                    )

                    # Execute the step
                    result = self.execute_workflow_step(step, execution_context)

                    # Only add to completed if successful
                    if step.status == AgentStatus.COMPLETED:
                        # Update project outputs based on agent type
                        self.update_project_outputs(step.agent_type, result)

                        completed_steps.append(step)
                        steps_executed_this_round += 1

                        # Add completion communication
                        self.add_agent_communication(
                            f"{step.agent_type.value} completed task: {step.task}"
                        )

                        # Update context for next steps
                        execution_context["collaboration_history"].append(
                            {
                                "step_id": step.id,
                                "agent": step.agent_type.value,
                                "output": result,
                            }
                        )

            # If no steps were executed this round, break to prevent infinite loops
            if steps_executed_this_round == 0:
                break

        # Phase 4: Final project summary
        return self.generate_project_summary()

    def are_dependencies_satisfied(
        self, step: WorkflowStep, completed_steps: List[WorkflowStep]
    ) -> bool:
        """Check if all dependencies for a step are satisfied"""
        if not step.dependencies:
            return True

        completed_ids = [
            s.id for s in completed_steps if s.status == AgentStatus.COMPLETED
        ]
        return all(dep_id in completed_ids for dep_id in step.dependencies)

    def add_agent_communication(self, message: str):
        """Add a message to the agent communication log"""
        self.agent_communications.append(
            {"timestamp": datetime.now().isoformat(), "message": message}
        )

    def update_project_outputs(self, agent_type: AgentType, result: Dict[str, Any]):
        """Update project outputs based on agent results"""

        if agent_type == AgentType.PROJECT_MANAGER:
            self.project_outputs["architecture"] = result.get("content", "")
        elif agent_type == AgentType.CODE_GENERATOR:
            self.project_outputs["code_files"].update(result.get("files", {}))
        elif agent_type == AgentType.UI_DESIGNER:
            self.project_outputs["ui_designs"].update(result.get("files", {}))
        elif agent_type == AgentType.TEST_WRITER:
            self.project_outputs["test_suites"].update(result.get("files", {}))
        elif agent_type == AgentType.DEBUGGER:
            self.project_outputs["debug_reports"][datetime.now().isoformat()] = (
                result.get("content", "")
            )

    def generate_project_summary(self) -> Dict[str, Any]:
        """Generate comprehensive project summary"""

        total_files = sum(
            len(files)
            for files in [
                self.project_outputs["code_files"],
                self.project_outputs["ui_designs"],
                self.project_outputs["test_suites"],
            ]
        )

        return {
            "project_info": self.current_project,
            "workflow_completed": True,
            "total_steps": len(self.workflow_steps),
            "completed_steps": len(
                [s for s in self.workflow_steps if s.status == AgentStatus.COMPLETED]
            ),
            "total_files_generated": total_files,
            "outputs": self.project_outputs,
            "collaboration_log": self.collaboration_log,
            "agent_communications": self.agent_communications,
            "execution_summary": f"Successfully orchestrated {len(self.workflow_steps)} agents to deliver complete project solution",
        }

    def get_real_time_status(self) -> Dict[str, Any]:
        """Get current status of all agents and workflow progress"""

        agent_statuses = {}
        for step in self.workflow_steps:
            agent_name = step.agent_type.value
            agent_statuses[agent_name] = {
                "status": step.status.value,
                "progress": step.progress,
                "current_task": step.task,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat()
                if step.completed_at
                else None,
            }

        overall_progress = (
            sum(step.progress for step in self.workflow_steps)
            / len(self.workflow_steps)
            if self.workflow_steps
            else 0
        )

        return {
            "overall_progress": overall_progress,
            "agent_statuses": agent_statuses,
            "recent_communications": self.agent_communications[
                -10:
            ],  # Last 10 messages
            "current_phase": self.get_current_phase(),
            "project_info": self.current_project,
        }

    def get_current_phase(self) -> str:
        """Determine current project phase based on active agents"""

        active_steps = [
            step
            for step in self.workflow_steps
            if step.status in [AgentStatus.WORKING, AgentStatus.ANALYZING]
        ]

        if not active_steps:
            completed_count = len(
                [s for s in self.workflow_steps if s.status == AgentStatus.COMPLETED]
            )
            if completed_count == len(self.workflow_steps):
                return "Project Complete"
            else:
                return "Initializing"

        current_agent = active_steps[0].agent_type
        phase_mapping = {
            AgentType.PROJECT_MANAGER: "Planning & Architecture",
            AgentType.CODE_GENERATOR: "Backend Development",
            AgentType.UI_DESIGNER: "Frontend Design",
            AgentType.TEST_WRITER: "Quality Assurance",
            AgentType.DEBUGGER: "Optimization & Debug",
        }

        return phase_mapping.get(current_agent, "In Progress")
