"""
Real AI API clients for multi-agent execution.

Provides unified interfaces for OpenAI, Anthropic, and Google AI APIs
with structured communication protocols and error handling.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
import json

# AI API clients
import openai
import anthropic
from google import genai
from google.genai import types

from schemas.artifacts import ArtifactBase, ArtifactType
from agents.base_agent import AgentInput, AgentOutput, AgentType

logger = logging.getLogger(__name__)


class AIClientConfig(BaseModel):
    """Configuration for AI clients"""
    
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get('OPENAI_API_KEY'))
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get('ANTHROPIC_API_KEY'))
    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.environ.get('GEMINI_API_KEY'))
    
    # Model configurations
    openai_model: str = Field(default="gpt-4o")
    claude_model: str = Field(default="claude-sonnet-4-20250514")
    gemini_model: str = Field(default="gemini-2.5-flash")
    
    # Request settings
    max_tokens: int = Field(default=4000)
    temperature: float = Field(default=0.7)
    timeout_seconds: int = Field(default=60)


class AgentPrompts:
    """Structured prompts for each agent type"""
    
    PROJECT_MANAGER_PROMPT = """You are a PROJECT MANAGER AI agent in a multi-agent development system.

Your role:
- Analyze project requirements and break them into concrete tasks
- Create detailed specifications and project plans
- Coordinate between other agents and manage dependencies
- Ensure project scope is well-defined and achievable

Task: {objective}
Context: {context}

Please provide a structured response with:
1. Project analysis and requirements breakdown
2. Task decomposition with clear dependencies
3. Success criteria and acceptance tests
4. Risk assessment and mitigation strategies
5. Recommended next steps for other agents

Format your response as JSON with these fields:
- "analysis": string
- "tasks": list of task objects with id, title, description, dependencies
- "success_criteria": list of criteria
- "risks": list of risk objects with description, impact, mitigation
- "next_steps": list of recommended actions
"""

    CODE_GENERATOR_PROMPT = """You are a CODE GENERATOR AI agent specializing in backend development and implementation.

Your role:
- Implement core business logic and algorithms
- Create scalable backend services and APIs
- Write clean, maintainable, and efficient code
- Follow best practices and coding standards

Task: {objective}
Context: {context}
Previous artifacts: {previous_artifacts}

Please provide a structured response with:
1. Technical approach and architecture decisions
2. Implementation plan with code structure
3. Key components and their responsibilities
4. Code examples and critical implementations
5. Testing recommendations

Format your response as JSON with these fields:
- "approach": string describing technical approach
- "architecture": object with components and structure
- "implementation": object with key code examples
- "components": list of component objects
- "testing_plan": string with testing recommendations
"""

    UI_DESIGNER_PROMPT = """You are a UI DESIGNER AI agent specializing in user experience and frontend development.

Your role:
- Design intuitive and accessible user interfaces
- Create responsive and modern UI components
- Ensure great user experience and usability
- Implement frontend functionality with modern frameworks

Task: {objective}
Context: {context}
Previous artifacts: {previous_artifacts}

Please provide a structured response with:
1. UI/UX design approach and principles
2. Component structure and layout design
3. User flow and interaction patterns
4. Styling and visual design decisions
5. Implementation recommendations

Format your response as JSON with these fields:
- "design_approach": string describing UI/UX strategy
- "components": list of UI component objects
- "user_flows": list of user flow descriptions
- "styling": object with design system decisions
- "implementation": string with frontend recommendations
"""

    TEST_WRITER_PROMPT = """You are a TEST WRITER AI agent specializing in quality assurance and testing.

Your role:
- Create comprehensive test strategies and test cases
- Design automated testing frameworks
- Ensure code quality and reliability
- Validate system functionality and performance

Task: {objective}
Context: {context}
Code to test: {code_artifacts}

Please provide a structured response with:
1. Testing strategy and approach
2. Test case design and coverage
3. Automated testing recommendations
4. Quality assurance checklist
5. Performance and security testing plans

Format your response as JSON with these fields:
- "strategy": string describing testing approach
- "test_cases": list of test case objects
- "automation": object with automation recommendations
- "quality_checklist": list of quality criteria
- "performance_tests": list of performance test descriptions
"""

    DEBUGGER_PROMPT = """You are a DEBUGGER AI agent specializing in code analysis and optimization.

Your role:
- Analyze code for bugs, issues, and improvements
- Optimize performance and resource usage
- Ensure code follows best practices
- Provide detailed code reviews and recommendations

Task: {objective}
Context: {context}
Code to analyze: {code_artifacts}

Please provide a structured response with:
1. Code analysis and issue identification
2. Performance optimization recommendations
3. Best practice improvements
4. Security considerations
5. Refactoring suggestions

Format your response as JSON with these fields:
- "analysis": string with overall code assessment
- "issues": list of issue objects with severity and fixes
- "optimizations": list of performance improvements
- "security": list of security recommendations
- "refactoring": list of refactoring suggestions
"""


class RealAIClients:
    """Real AI API clients for multi-agent execution"""
    
    def __init__(self, config: Optional[AIClientConfig] = None):
        self.config = config or AIClientConfig()
        
        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_client = None
        
        self._init_clients()
    
    def _init_clients(self):
        """Initialize AI API clients"""
        try:
            if self.config.openai_api_key:
                self.openai_client = openai.OpenAI(api_key=self.config.openai_api_key)
                logger.info("OpenAI client initialized")
            
            if self.config.anthropic_api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
                logger.info("Anthropic client initialized")
            
            if self.config.gemini_api_key:
                self.gemini_client = genai.Client(api_key=self.config.gemini_api_key)
                logger.info("Gemini client initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize AI clients: {e}")
    
    async def call_claude_agent(self, agent_input: AgentInput, agent_type: AgentType) -> AgentOutput:
        """Execute Claude agent for project management and debugging"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not available")
        
        try:
            # Select appropriate prompt
            if agent_type == AgentType.PROJECT_MANAGER:
                prompt = AgentPrompts.PROJECT_MANAGER_PROMPT.format(
                    objective=agent_input.objective,
                    context=agent_input.context
                )
            elif agent_type == AgentType.DEBUGGER:
                code_artifacts = "\n".join(agent_input.dependency_artifacts) if agent_input.dependency_artifacts else "No code provided"
                prompt = AgentPrompts.DEBUGGER_PROMPT.format(
                    objective=agent_input.objective,
                    context=agent_input.context,
                    code_artifacts=code_artifacts
                )
            else:
                raise ValueError(f"Claude not configured for agent type: {agent_type}")
            
            # Call Claude API
            response = self.anthropic_client.messages.create(
                model=self.config.claude_model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            
            # Parse JSON response
            try:
                result_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback if not JSON
                result_data = {"analysis": content, "status": "completed"}
            
            return AgentOutput(
                request_id=agent_input.request_id,
                task_id=agent_input.task_id,
                agent_type=agent_type,
                status="completed",
                result=result_data,
                reasoning=f"Claude {agent_type.value} analysis completed",
                confidence=0.9,
                artifacts_produced=[],
                next_recommended_agents=[],
                processing_time_seconds=30.0
            )
            
        except Exception as e:
            logger.error(f"Claude agent execution failed: {e}")
            return AgentOutput(
                request_id=agent_input.request_id,
                task_id=agent_input.task_id,
                agent_type=agent_type,
                status="failed",
                result={"error": str(e)},
                reasoning=f"Claude execution failed: {e}",
                confidence=0.0,
                artifacts_produced=[],
                next_recommended_agents=[],
                processing_time_seconds=0.0
            )
    
    async def call_gpt4_agent(self, agent_input: AgentInput, agent_type: AgentType) -> AgentOutput:
        """Execute GPT-4 agent for code generation and testing"""
        if not self.openai_client:
            raise ValueError("OpenAI client not available")
        
        try:
            # Select appropriate prompt
            if agent_type == AgentType.CODE_GENERATOR:
                previous_artifacts = "\n".join(agent_input.dependency_artifacts) if agent_input.dependency_artifacts else "No previous artifacts"
                prompt = AgentPrompts.CODE_GENERATOR_PROMPT.format(
                    objective=agent_input.objective,
                    context=agent_input.context,
                    previous_artifacts=previous_artifacts
                )
            elif agent_type == AgentType.TEST_WRITER:
                code_artifacts = "\n".join(agent_input.dependency_artifacts) if agent_input.dependency_artifacts else "No code provided"
                prompt = AgentPrompts.TEST_WRITER_PROMPT.format(
                    objective=agent_input.objective,
                    context=agent_input.context,
                    code_artifacts=code_artifacts
                )
            else:
                raise ValueError(f"GPT-4 not configured for agent type: {agent_type}")
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": f"You are a {agent_type.value} AI agent. Provide structured, actionable responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                result_data = json.loads(content)
            except json.JSONDecodeError:
                result_data = {"implementation": content, "status": "completed"}
            
            return AgentOutput(
                request_id=agent_input.request_id,
                task_id=agent_input.task_id,
                agent_type=agent_type,
                status="completed",
                result=result_data,
                reasoning=f"GPT-4 {agent_type.value} implementation completed",
                confidence=0.9,
                artifacts_produced=[],
                next_recommended_agents=[],
                processing_time_seconds=25.0
            )
            
        except Exception as e:
            logger.error(f"GPT-4 agent execution failed: {e}")
            return AgentOutput(
                request_id=agent_input.request_id,
                task_id=agent_input.task_id,
                agent_type=agent_type,
                status="failed",
                result={"error": str(e)},
                reasoning=f"GPT-4 execution failed: {e}",
                confidence=0.0,
                artifacts_produced=[],
                next_recommended_agents=[],
                processing_time_seconds=0.0
            )
    
    async def call_gemini_agent(self, agent_input: AgentInput, agent_type: AgentType) -> AgentOutput:
        """Execute Gemini agent for UI design"""
        if not self.gemini_client:
            raise ValueError("Gemini client not available")
        
        try:
            # UI Designer prompt
            if agent_type == AgentType.UI_DESIGNER:
                previous_artifacts = "\n".join(agent_input.dependency_artifacts) if agent_input.dependency_artifacts else "No previous artifacts"
                prompt = AgentPrompts.UI_DESIGNER_PROMPT.format(
                    objective=agent_input.objective,
                    context=agent_input.context,
                    previous_artifacts=previous_artifacts
                )
            else:
                raise ValueError(f"Gemini not configured for agent type: {agent_type}")
            
            # Call Gemini API
            response = self.gemini_client.models.generate_content(
                model=self.config.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens,
                    response_mime_type="application/json"
                )
            )
            
            content = response.text
            
            # Parse JSON response
            try:
                result_data = json.loads(content)
            except json.JSONDecodeError:
                result_data = {"design_approach": content, "status": "completed"}
            
            return AgentOutput(
                request_id=agent_input.request_id,
                task_id=agent_input.task_id,
                agent_type=agent_type,
                status="completed",
                result=result_data,
                reasoning=f"Gemini {agent_type.value} design completed",
                confidence=0.9,
                artifacts_produced=[],
                next_recommended_agents=[],
                processing_time_seconds=20.0
            )
            
        except Exception as e:
            logger.error(f"Gemini agent execution failed: {e}")
            return AgentOutput(
                request_id=agent_input.request_id,
                task_id=agent_input.task_id,
                agent_type=agent_type,
                status="failed",
                result={"error": str(e)},
                reasoning=f"Gemini execution failed: {e}",
                confidence=0.0,
                artifacts_produced=[],
                next_recommended_agents=[],
                processing_time_seconds=0.0
            )
    
    async def execute_agent(self, agent_input: AgentInput, agent_type: AgentType) -> AgentOutput:
        """Execute appropriate agent based on type"""
        logger.info(f"Executing {agent_type.value} agent for task {agent_input.task_id}")
        
        # Route to appropriate AI model
        if agent_type in [AgentType.PROJECT_MANAGER, AgentType.DEBUGGER]:
            return await self.call_claude_agent(agent_input, agent_type)
        elif agent_type in [AgentType.CODE_GENERATOR, AgentType.TEST_WRITER]:
            return await self.call_gpt4_agent(agent_input, agent_type)
        elif agent_type == AgentType.UI_DESIGNER:
            return await self.call_gemini_agent(agent_input, agent_type)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    def get_available_agents(self) -> List[AgentType]:
        """Get list of available agents based on API keys"""
        available = []
        
        if self.anthropic_client:
            available.extend([AgentType.PROJECT_MANAGER, AgentType.DEBUGGER])
        
        if self.openai_client:
            available.extend([AgentType.CODE_GENERATOR, AgentType.TEST_WRITER])
        
        if self.gemini_client:
            available.append(AgentType.UI_DESIGNER)
        
        return available
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all AI clients"""
        return {
            "openai": self.openai_client is not None,
            "anthropic": self.anthropic_client is not None,
            "gemini": self.gemini_client is not None
        }