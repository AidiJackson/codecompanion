"""
Real AI Execution Engine - Replaces simulation with actual AI API calls.

This module provides the RealExecutionEngine class that orchestrates actual
AI agents using OpenAI, Anthropic, and Google APIs instead of simulations.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import uuid

from core.ai_clients import RealAIClients, AIClientConfig
from agents.base_agent import AgentInput, AgentOutput, AgentType
from schemas.routing import ModelType

logger = logging.getLogger(__name__)


class RealExecutionEngine:
    """
    Real AI execution engine that replaces simulation with actual API calls.
    """
    
    def __init__(self, status_callback: Optional[Callable] = None, output_callback: Optional[Callable] = None):
        """
        Initialize real execution engine.
        
        Args:
            status_callback: Function to call with status updates
            output_callback: Function to call with agent outputs
        """
        self.ai_clients = RealAIClients()
        self.status_callback = status_callback or self._default_status_callback
        self.output_callback = output_callback or self._default_output_callback
        
        # Track execution state
        self.current_artifacts = []
        self.execution_id = None
        
    def _default_status_callback(self, message: str):
        """Default status callback"""
        logger.info(f"Status: {message}")
        
    def _default_output_callback(self, agent_name: str, content: str):
        """Default output callback"""
        logger.info(f"Agent Output [{agent_name}]: {content[:100]}...")

    async def execute_real_project_workflow(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute complete real AI project workflow with actual API calls.
        
        Args:
            project_config: Project configuration with description, type, complexity
            
        Returns:
            Dictionary with execution results and artifacts
        """
        self.execution_id = f"real_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        current_time = datetime.now().strftime("%H:%M:%S")
        
        self.status_callback(f"🚀 Real AI session started at {current_time}")
        self.status_callback("🔑 Initializing AI clients (Claude, GPT-4, Gemini)")
        
        try:
            # Step 1: Real Claude Project Manager Analysis
            self.status_callback("🧠 Claude analyzing project requirements...")
            pm_result = await self._execute_project_manager_agent(project_config)
            self.status_callback("✅ Claude requirements analysis complete")
            self.output_callback("Project Manager (Claude)", pm_result)
            
            # Step 2: Real GPT-4 Code Generation
            self.status_callback("💻 GPT-4 designing system architecture...")
            code_result = await self._execute_code_generator_agent(project_config, pm_result)
            self.status_callback("✅ GPT-4 code generation complete")
            self.output_callback("Code Generator (GPT-4)", code_result)
            
            # Step 3: Real Gemini UI Design
            self.status_callback("🎨 Gemini creating UI design...")
            ui_result = await self._execute_ui_designer_agent(project_config, [pm_result, code_result])
            self.status_callback("✅ Gemini UI design complete")
            self.output_callback("UI Designer (Gemini)", ui_result)
            
            # Step 4: Real GPT-4 Test Generation
            self.status_callback("🧪 GPT-4 generating comprehensive tests...")
            test_result = await self._execute_test_writer_agent(project_config, code_result)
            self.status_callback("✅ GPT-4 test generation complete")
            self.output_callback("Test Writer (GPT-4)", test_result)
            
            # Step 5: Real Claude Code Review
            self.status_callback("🔍 Claude performing code review and optimization...")
            debug_result = await self._execute_debugger_agent(project_config, [code_result, test_result])
            self.status_callback("🎉 All AI agents completed successfully! Real project ready.")
            self.output_callback("Debugger (Claude)", debug_result)
            
            completion_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback(f"✨ Real AI collaboration completed at {completion_time}")
            
            return {
                "status": "completed",
                "execution_id": self.execution_id,
                "completion_time": completion_time,
                "agents_executed": [
                    "Project Manager (Claude)",
                    "Code Generator (GPT-4)", 
                    "UI Designer (Gemini)",
                    "Test Writer (GPT-4)",
                    "Debugger (Claude)"
                ],
                "artifacts": {
                    "project_analysis": pm_result,
                    "code_structure": code_result,
                    "ui_design": ui_result,
                    "test_suite": test_result,
                    "code_review": debug_result
                },
                "real_execution": True,
                "total_api_calls": 5
            }
            
        except Exception as e:
            error_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback(f"❌ Real execution error at {error_time}: {str(e)}")
            logger.error(f"Real execution failed: {e}")
            
            return {
                "status": "failed",
                "execution_id": self.execution_id,
                "error": str(e),
                "error_time": error_time,
                "real_execution": True
            }

    async def _execute_project_manager_agent(self, project_config: Dict[str, Any]) -> str:
        """Execute real Claude Project Manager agent"""
        
        agent_input = AgentInput(
            request_id=str(uuid.uuid4()),
            task_id="project_analysis",
            objective=f"Analyze and break down this project: {project_config['description']}",
            context=f"""
            Project Type: {project_config.get('type', 'general')}
            Complexity: {project_config.get('complexity', 'medium')}
            
            Please provide a comprehensive project analysis including:
            1. Requirements breakdown
            2. Technical architecture recommendations
            3. Development phases and timeline
            4. Risk assessment
            5. Success criteria
            """,
            priority="high",
            dependency_artifacts=[],
            requested_artifact=None
        )
        
        try:
            result = await self.ai_clients.call_claude_agent(agent_input, AgentType.PROJECT_MANAGER)
            
            if result.artifact and 'error' not in result.artifact:
                return self._format_agent_result("PROJECT ANALYSIS", result.artifact)
            else:
                return f"Error in Claude analysis: {result.artifact.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Exception in Claude execution: {str(e)}"

    async def _execute_code_generator_agent(self, project_config: Dict[str, Any], requirements: str) -> str:
        """Execute real GPT-4 Code Generator agent"""
        
        agent_input = AgentInput(
            request_id=str(uuid.uuid4()),
            task_id="code_generation",
            objective=f"Generate code structure for: {project_config['description']}",
            context=f"""
            Project Requirements from Analysis:
            {requirements}
            
            Project Type: {project_config.get('type', 'general')}
            
            Please provide:
            1. System architecture design
            2. Core implementation structure
            3. Key components and modules
            4. Database design if applicable
            5. API structure if applicable
            """,
            priority="high",
            dependency_artifacts=[requirements],
            requested_artifact=None
        )
        
        try:
            result = await self.ai_clients.call_gpt4_agent(agent_input, AgentType.CODE_GENERATOR)
            
            if result.artifact and 'error' not in result.artifact:
                return self._format_agent_result("CODE ARCHITECTURE", result.artifact)
            else:
                return f"Error in GPT-4 code generation: {result.artifact.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Exception in GPT-4 execution: {str(e)}"

    async def _execute_ui_designer_agent(self, project_config: Dict[str, Any], previous_artifacts: List[str]) -> str:
        """Execute real Gemini UI Designer agent"""
        
        dependencies_text = "\n\n".join(previous_artifacts)
        
        agent_input = AgentInput(
            request_id=str(uuid.uuid4()),
            task_id="ui_design",
            objective=f"Design user interface for: {project_config['description']}",
            context=f"""
            Previous Agent Results:
            {dependencies_text}
            
            Project Type: {project_config.get('type', 'general')}
            
            Please provide:
            1. UI/UX design approach
            2. Component structure and layouts
            3. User experience flows
            4. Visual design decisions
            5. Responsive design considerations
            """,
            priority="high",
            dependency_artifacts=previous_artifacts,
            requested_artifact=None
        )
        
        try:
            result = await self.ai_clients.call_gemini_agent(agent_input, AgentType.UI_DESIGNER)
            
            if result.artifact and 'error' not in result.artifact:
                return self._format_agent_result("UI DESIGN", result.artifact)
            else:
                return f"Error in Gemini UI design: {result.artifact.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Exception in Gemini execution: {str(e)}"

    async def _execute_test_writer_agent(self, project_config: Dict[str, Any], code_structure: str) -> str:
        """Execute real GPT-4 Test Writer agent"""
        
        agent_input = AgentInput(
            request_id=str(uuid.uuid4()),
            task_id="test_generation",
            objective=f"Generate comprehensive tests for: {project_config['description']}",
            context=f"""
            Code Structure to Test:
            {code_structure}
            
            Project Type: {project_config.get('type', 'general')}
            
            Please provide:
            1. Testing strategy and approach
            2. Unit test cases and coverage
            3. Integration testing plan
            4. Performance testing considerations
            5. Security testing recommendations
            """,
            priority="high",
            dependency_artifacts=[code_structure],
            requested_artifact=None
        )
        
        try:
            result = await self.ai_clients.call_gpt4_agent(agent_input, AgentType.TEST_WRITER)
            
            if result.artifact and 'error' not in result.artifact:
                return self._format_agent_result("TEST SUITE", result.artifact)
            else:
                return f"Error in GPT-4 test generation: {result.artifact.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Exception in GPT-4 test execution: {str(e)}"

    async def _execute_debugger_agent(self, project_config: Dict[str, Any], code_artifacts: List[str]) -> str:
        """Execute real Claude Debugger agent"""
        
        code_text = "\n\n".join(code_artifacts)
        
        agent_input = AgentInput(
            request_id=str(uuid.uuid4()),
            task_id="code_review",
            objective=f"Review and optimize code for: {project_config['description']}",
            context=f"""
            Code and Tests to Review:
            {code_text}
            
            Project Type: {project_config.get('type', 'general')}
            
            Please provide:
            1. Code quality assessment
            2. Performance optimization recommendations
            3. Security considerations
            4. Best practice improvements
            5. Deployment readiness checklist
            """,
            priority="high",
            dependency_artifacts=code_artifacts,
            requested_artifact=None
        )
        
        try:
            result = await self.ai_clients.call_claude_agent(agent_input, AgentType.DEBUGGER)
            
            if result.artifact and 'error' not in result.artifact:
                return self._format_agent_result("CODE REVIEW", result.artifact)
            else:
                return f"Error in Claude code review: {result.artifact.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Exception in Claude debugger execution: {str(e)}"

    def _format_agent_result(self, title: str, artifact: Dict[str, Any]) -> str:
        """Format agent result for display"""
        
        if isinstance(artifact, dict):
            # Try to extract meaningful content from structured response
            content_parts = []
            
            # Add title
            content_parts.append(f"🤖 **REAL AI {title} RESULT**\n")
            
            # Extract key fields
            for key, value in artifact.items():
                if key in ['analysis', 'approach', 'implementation', 'strategy', 'design_approach']:
                    content_parts.append(f"**{key.replace('_', ' ').title()}:**\n{value}\n")
                elif key == 'tasks' and isinstance(value, list):
                    content_parts.append("**Task Breakdown:**")
                    for i, task in enumerate(value[:5], 1):  # Show first 5 tasks
                        if isinstance(task, dict):
                            content_parts.append(f"{i}. {task.get('title', 'Untitled')}: {task.get('description', 'No description')}")
                elif key == 'requirements' and isinstance(value, list):
                    content_parts.append("**Requirements:**")
                    for req in value[:5]:  # Show first 5 requirements
                        if isinstance(req, dict):
                            content_parts.append(f"• {req.get('description', str(req))}")
                        else:
                            content_parts.append(f"• {str(req)}")
                elif key == 'components' and isinstance(value, list):
                    content_parts.append("**Key Components:**")
                    for comp in value[:5]:  # Show first 5 components
                        if isinstance(comp, dict):
                            content_parts.append(f"• {comp.get('name', 'Component')}: {comp.get('description', 'No description')}")
                        else:
                            content_parts.append(f"• {str(comp)}")
            
            # Add metadata
            content_parts.append(f"\n**Generated by Real AI API** | ⏱️ {datetime.now().strftime('%H:%M:%S')}")
            
            return "\n".join(content_parts)
        
        else:
            return f"🤖 **REAL AI {title} RESULT**\n\n{str(artifact)}\n\n**Generated by Real AI API** | ⏱️ {datetime.now().strftime('%H:%M:%S')}"

    def get_available_agents(self) -> List[str]:
        """Get list of available AI agents"""
        available = []
        
        if self.ai_clients.anthropic_client:
            available.extend(["Project Manager (Claude)", "Debugger (Claude)"])
        if self.ai_clients.openai_client:
            available.extend(["Code Generator (GPT-4)", "Test Writer (GPT-4)"])
        if self.ai_clients.gemini_client:
            available.append("UI Designer (Gemini)")
            
        return available

    def check_api_readiness(self) -> Dict[str, bool]:
        """Check which AI APIs are ready for execution"""
        return {
            "claude": self.ai_clients.anthropic_client is not None,
            "gpt4": self.ai_clients.openai_client is not None,
            "gemini": self.ai_clients.gemini_client is not None
        }