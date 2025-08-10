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
from schemas.artifacts import ArtifactType
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
    
    def add_real_timeline_event(self, timestamp: str, message: str):
        """Add real timeline event with actual current time for live UI display"""
        import streamlit as st
        
        if 'live_timeline' not in st.session_state:
            st.session_state.live_timeline = []
        
        # Use actual current timestamp, not simulation
        real_event = {
            'time': timestamp,  # Real current time
            'message': message,
            'real_timestamp': datetime.now(),
            'is_real': True  # Flag to distinguish from simulation
        }
        
        st.session_state.live_timeline.append(real_event)
        
        # Force immediate UI update
        try:
            st.rerun()
        except:
            pass  # Handle case where rerun is called during execution
    
    def add_real_artifact(self, title: str, content: str):
        """Add real artifact with actual AI-generated content for live display"""
        import streamlit as st
        
        if 'real_artifacts' not in st.session_state:
            st.session_state.real_artifacts = []
        
        if content and len(str(content).strip()) > 0:  # Only add non-empty content
            artifact = {
                'title': title,
                'content': str(content),
                'created_at': datetime.now(),
                'formatted_time': datetime.now().strftime("%H:%M:%S"),
                'word_count': len(str(content).split()),
                'is_real': True,
                'api_generated': True
            }
            
            st.session_state.real_artifacts.append(artifact)
            
            # Update total artifacts counter for live display
            st.session_state.total_artifacts = len(st.session_state.real_artifacts)

    async def execute_real_project_workflow(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute complete real AI project workflow with actual API calls and live UI updates.
        
        Args:
            project_config: Project configuration with description, type, complexity
            
        Returns:
            Dictionary with execution results and artifacts
        """
        self.execution_id = f"real_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize session state for real-time tracking
        import streamlit as st
        if 'live_timeline' not in st.session_state:
            st.session_state.live_timeline = []
        if 'real_artifacts' not in st.session_state:
            st.session_state.real_artifacts = []
        
        # Clear any previous simulation data
        st.session_state.live_timeline.clear()
        st.session_state.real_artifacts.clear()
        
        start_time = datetime.now()
        current_time = start_time.strftime("%H:%M:%S")
        
        self.status_callback(f"🚀 Real AI multi-agent session started at {current_time}")
        self.add_real_timeline_event(current_time, "🚀 Real AI session initialized")
        
        try:
            # Step 1: Real Claude Project Manager Analysis
            current_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback("🧠 Claude agent started - Requirements Analysis")
            self.add_real_timeline_event(current_time, "🧠 Claude agent started - Requirements Analysis")
            
            claude_prompt = f"""
            Analyze this project thoroughly:
            Description: {project_config.get('description')}
            Type: {project_config.get('type')} 
            Complexity: {project_config.get('complexity')}
            
            Provide detailed requirements analysis, technical recommendations, and project structure.
            """
            
            pm_result = await self._execute_project_manager_agent(project_config, claude_prompt)
            completion_time = datetime.now().strftime("%H:%M:%S")
            
            self.status_callback("✅ Claude requirements analysis complete")
            self.add_real_timeline_event(completion_time, "✅ Claude requirements analysis complete")
            self.add_real_artifact("Requirements Analysis by Claude", pm_result)
            self.output_callback("Project Manager (Claude)", pm_result)
            
            # Step 2: Real GPT-4 Code Generation
            current_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback("🏗️ GPT-4 agent started - System Architecture")
            self.add_real_timeline_event(current_time, "🏗️ GPT-4 agent started - System Architecture")
            
            gpt4_prompt = f"""
            Based on Claude's analysis: {pm_result[:800]}...
            
            Design the complete system architecture including:
            - Technology stack and frameworks
            - Database design and data models  
            - API structure and endpoints
            - Component architecture and relationships
            """
            
            code_result = await self._execute_code_generator_agent(project_config, gpt4_prompt)
            completion_time = datetime.now().strftime("%H:%M:%S")
            
            self.status_callback("✅ GPT-4 architecture design complete")
            self.add_real_timeline_event(completion_time, "✅ GPT-4 architecture design complete")
            self.add_real_artifact("System Architecture by GPT-4", code_result)
            self.output_callback("Code Generator (GPT-4)", code_result)
            
            # Step 3: Real Gemini UI Design
            current_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback("🎨 Gemini agent started - UI Design")
            self.add_real_timeline_event(current_time, "🎨 Gemini agent started - UI Design")
            
            gemini_prompt = f"""
            Create comprehensive UI design for: {project_config.get('description')}
            Architecture: {code_result[:600]}...
            
            Design user interface including:
            - Screen layouts and navigation
            - Visual design and branding
            - User experience flow
            - Component specifications
            """
            
            ui_result = await self._execute_ui_designer_agent(project_config, gemini_prompt)
            completion_time = datetime.now().strftime("%H:%M:%S")
            
            self.status_callback("✅ Gemini UI design complete")
            self.add_real_timeline_event(completion_time, "✅ Gemini UI design complete")
            self.add_real_artifact("UI Design by Gemini", ui_result)
            self.output_callback("UI Designer (Gemini)", ui_result)
            
            # Step 4: Real GPT-4 Test Generation
            current_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback("🧪 GPT-4 generating comprehensive tests...")
            self.add_real_timeline_event(current_time, "🧪 GPT-4 started - Test Generation")
            
            test_result = await self._execute_test_writer_agent(project_config, code_result)
            completion_time = datetime.now().strftime("%H:%M:%S")
            
            self.status_callback("✅ GPT-4 test generation complete")
            self.add_real_timeline_event(completion_time, "✅ GPT-4 test generation complete")
            self.add_real_artifact("Test Suite by GPT-4", test_result)
            self.output_callback("Test Writer (GPT-4)", test_result)
            
            # Step 5: Real Claude Code Review
            current_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback("🔍 Claude performing code review and optimization...")
            self.add_real_timeline_event(current_time, "🔍 Claude started - Code Review")
            
            debug_result = await self._execute_debugger_agent(project_config, [code_result, test_result])
            completion_time = datetime.now().strftime("%H:%M:%S")
            
            self.status_callback("✅ Claude code review complete")
            self.add_real_timeline_event(completion_time, "✅ Claude code review complete")
            self.add_real_artifact("Code Review by Claude", debug_result)
            self.output_callback("Debugger (Claude)", debug_result)
            
            # Final completion
            final_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback("🎉 Real AI multi-agent collaboration completed!")
            self.add_real_timeline_event(final_time, "🎉 Multi-agent collaboration completed")
            
            return {
                "status": "completed",
                "execution_id": self.execution_id,
                "completion_time": final_time,
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
                "total_api_calls": 5,
                "timeline_events": len(st.session_state.live_timeline),
                "real_artifacts": len(st.session_state.real_artifacts)
            }
            
        except Exception as e:
            error_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback(f"❌ Execution failed at {error_time}: {str(e)}")
            self.add_real_timeline_event(error_time, f"❌ Error: {str(e)}")
            return {
                "status": "failed",
                "execution_id": self.execution_id,
                "error": str(e),
                "error_time": error_time,
                "real_execution": True
            }

    async def execute_simple_workflow(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple workflow that bypasses complex validation and calls OpenAI directly.
        This is a fallback method when complex agent validation fails.
        """
        self.execution_id = f"simple_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        current_time = datetime.now().strftime("%H:%M:%S")
        
        self.status_callback(f"🚀 Simple AI workflow started at {current_time}")
        
        try:
            artifacts = []
            
            # Step 1: Requirements Analysis
            self.status_callback("🧠 Analyzing project requirements...")
            
            prompt1 = f"""
            Project: {project_config.get('description')}
            Type: {project_config.get('type')}
            Complexity: {project_config.get('complexity')}
            
            Provide a detailed project analysis including features, technical requirements, and development plan.
            """
            
            result1 = await self.simple_openai_call("Requirements Analyst", prompt1)
            artifacts.append(("Requirements Analysis", result1))
            self.output_callback("Requirements Analyst", result1)
            self.status_callback("✅ Requirements analysis complete")
            
            # Step 2: Architecture Design
            self.status_callback("🏗️ Designing system architecture...")
            
            prompt2 = f"""
            Based on these requirements: {result1[:500]}...
            
            Design the system architecture including:
            - Technology stack
            - Component structure  
            - Database design
            - API endpoints
            """
            
            result2 = await self.simple_openai_call("System Architect", prompt2)
            artifacts.append(("System Architecture", result2))
            self.output_callback("System Architect", result2)
            self.status_callback("✅ Architecture design complete")
            
            # Step 3: Code Structure
            self.status_callback("💻 Generating code structure...")
            
            prompt3 = f"""
            Create the code structure for: {project_config.get('description')}
            Architecture: {result2[:500]}...
            
            Provide file structure, key components, and sample code.
            """
            
            result3 = await self.simple_openai_call("Code Generator", prompt3)
            artifacts.append(("Code Structure", result3))
            self.output_callback("Code Generator", result3)
            self.status_callback("✅ Code generation complete")

            completion_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback(f"✨ Simple AI workflow completed at {completion_time}")
            
            return {
                "status": "completed",
                "execution_id": self.execution_id,
                "completion_time": completion_time,
                "agents_executed": ["Requirements Analyst", "System Architect", "Code Generator"],
                "artifacts": dict(artifacts),
                "real_execution": True,
                "total_api_calls": 3
            }
            
        except Exception as e:
            error_time = datetime.now().strftime("%H:%M:%S")
            self.status_callback(f"❌ Simple execution failed at {error_time}: {str(e)}")
            return {
                "status": "failed", 
                "execution_id": self.execution_id,
                "error": str(e),
                "error_time": error_time,
                "real_execution": True
            }
    
    async def simple_openai_call(self, role: str, prompt: str) -> str:
        """Simple OpenAI call without complex validation"""
        try:
            if not self.ai_clients.openai_client:
                return f"Error: OpenAI client not available. Please provide API key."
            
            response = self.ai_clients.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an expert {role}."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content or f"No response from {role}"
        except Exception as e:
            return f"Error in {role}: {str(e)}"

    async def _execute_project_manager_agent(self, project_config: Dict[str, Any], prompt: str) -> str:
        """Execute real Claude Project Manager agent"""
        
        agent_input = AgentInput(
            request_id=str(uuid.uuid4()),
            task_id="project_analysis",
            objective=f"Analyze and break down this project: {project_config['description']}",
            context=prompt,
            priority="high",
            dependency_artifacts=[],
            requested_artifact=ArtifactType.SPEC_DOC,
            correlation_id=str(uuid.uuid4()),
            max_processing_time=300
        )
        
        try:
            result = await self.ai_clients.call_claude_agent(agent_input, AgentType.PROJECT_MANAGER)
            
            if result.artifact and 'error' not in result.artifact:
                return self._format_agent_result("PROJECT ANALYSIS", result.artifact)
            else:
                return f"Error in Claude analysis: {result.artifact.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Exception in Claude execution: {str(e)}"

    async def _execute_code_generator_agent(self, project_config: Dict[str, Any], prompt: str) -> str:
        """Execute real GPT-4 Code Generator agent"""
        
        agent_input = AgentInput(
            request_id=str(uuid.uuid4()),
            task_id="code_generation",
            objective=f"Generate code structure for: {project_config['description']}",
            context=prompt,
            priority="high",
            dependency_artifacts=[],
            requested_artifact=ArtifactType.CODE_PATCH,
            correlation_id=str(uuid.uuid4()),
            max_processing_time=300
        )
        
        try:
            result = await self.ai_clients.call_gpt4_agent(agent_input, AgentType.CODE_GENERATOR)
            
            if result.artifact and 'error' not in result.artifact:
                return self._format_agent_result("CODE ARCHITECTURE", result.artifact)
            else:
                return f"Error in GPT-4 code generation: {result.artifact.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Exception in GPT-4 execution: {str(e)}"

    async def _execute_ui_designer_agent(self, project_config: Dict[str, Any], prompt: str) -> str:
        """Execute real Gemini UI Designer agent"""
        
        agent_input = AgentInput(
            request_id=str(uuid.uuid4()),
            task_id="ui_design",
            objective=f"Design user interface for: {project_config['description']}",
            context=prompt,
            priority="high",
            dependency_artifacts=[],
            requested_artifact=ArtifactType.DESIGN_DOC,
            correlation_id=str(uuid.uuid4()),
            max_processing_time=300
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
            requested_artifact=ArtifactType.TEST_PLAN,
            correlation_id=str(uuid.uuid4()),
            max_processing_time=300
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
            requested_artifact=ArtifactType.EVAL_REPORT,
            correlation_id=str(uuid.uuid4()),
            max_processing_time=300
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