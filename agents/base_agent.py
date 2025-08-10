from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import os
import asyncio
from core.model_orchestrator import orchestrator, AgentType

class BaseAgent(ABC):
    """Base class for all AI agents in the multi-agent system"""
    
    def __init__(self, name: str, role: str, specialization: str, agent_type: AgentType):
        self.name = name
        self.role = role
        self.specialization = specialization
        self.agent_type = agent_type
        self.agent_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now()
        self.conversation_history: List[Dict] = []
        
        # Multi-model integration
        self.preferred_model = agent_type.value[0] if agent_type else "gpt4"
        self.model_assignments = {
            AgentType.PROJECT_MANAGER: "claude",
            AgentType.CODE_GENERATOR: "gpt4", 
            AgentType.UI_DESIGNER: "gpt4",
            AgentType.TEST_WRITER: "gemini",
            AgentType.DEBUGGER: "claude"
        }
    
    @abstractmethod
    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user request and return response with potential handoffs"""
        pass
    
    @abstractmethod
    def process_handoff(self, handoff_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a handoff from another agent"""
        pass
    
    def get_system_prompt(self) -> str:
        """Get the system prompt that defines this agent's behavior"""
        return f"""
        You are {self.name}, a specialized AI agent with the role of {self.role}.
        Your specialization is: {self.specialization}
        
        You work as part of a multi-agent development team. When responding:
        1. Stay within your area of expertise
        2. Provide detailed, actionable responses
        3. Suggest handoffs to other agents when appropriate
        4. Generate actual code when requested, not just descriptions
        5. Maintain context awareness across conversations
        
        Available agents for handoffs:
        - project_manager: Project planning, requirements, coordination
        - code_generator: Backend development, algorithms, APIs
        - ui_designer: Frontend, user interface, user experience
        - test_writer: Test cases, quality assurance, validation
        - debugger: Code analysis, bug fixes, optimization
        
        Always provide helpful, professional responses that move the project forward.
        """
    
    async def call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7, task_context: str = "") -> str:
        """Make a call to the optimal AI model through orchestrator"""
        from utils.error_handler import safe_api_call, circuit_breaker
        
        @circuit_breaker
        def _make_api_call():
            # Get optimal model for this agent type
            model_name = orchestrator.get_optimal_model(self.agent_type, task_context)
            
            # Generate response using the orchestrator
            return orchestrator.generate_response(
                model_name=model_name,
                messages=messages,
                agent_type=self.agent_type,
                task_id=f"{self.agent_id}_{int(datetime.now().timestamp())}"
            )
        
        result = safe_api_call(_make_api_call, service_name=f"agent_{self.name.lower().replace(' ', '_')}")
        
        if result['success']:
            return result.get('data', {}).get('content', result.get('content', 'No response'))
        else:
            return result.get('content', f"Error: {result.get('error', 'Unknown error')}")
    
    def call_llm_sync(self, messages: List[Dict[str, str]], temperature: float = 0.7, task_context: str = "") -> str:
        """Synchronous version of call_llm with comprehensive error handling"""
        from utils.error_handler import safe_api_call, circuit_breaker, validate_input, get_error_help_message
        
        try:
            # Validate input messages
            if not messages or not isinstance(messages, list):
                return "Error: Invalid message format provided."
            
            # Validate message content length
            total_content = " ".join([msg.get('content', '') for msg in messages])
            validation = validate_input(total_content, max_length=50000)  # 50k char limit
            
            if not validation['valid']:
                return f"Error: {validation['error']}"
            
            @circuit_breaker
            def _make_sync_api_call():
                # Get optimal model for this agent type
                model_name = orchestrator.get_optimal_model(self.agent_type, task_context)
                
                # Generate response using the orchestrator
                response = asyncio.run(orchestrator.generate_response(
                    model_name=model_name,
                    messages=messages,
                    agent_type=self.agent_type,
                    task_id=f"{self.agent_id}_{int(datetime.now().timestamp())}"
                ))
                
                return response
            
            result = safe_api_call(
                _make_sync_api_call, 
                service_name=f"agent_{self.name.lower().replace(' ', '_')}",
                timeout=30
            )
            
            if result['success']:
                response_data = result.get('data', {})
                if isinstance(response_data, dict):
                    return response_data.get('content', str(response_data))
                else:
                    return str(response_data)
            else:
                error_help = get_error_help_message(result.get('error_type', 'unknown'))
                return f"[{self.name}] {error_help}"
                
        except Exception as e:
            from utils.error_handler import logger
            logger.error(f"Error in call_llm_sync for {self.name}: {str(e)}")
            return f"[{self.name}] Unable to process request due to a technical error. Please try again or contact support."
    
    def add_to_history(self, request: str, response: str):
        """Add interaction to conversation history"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "request": request,
            "response": response,
            "agent": self.name
        })
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get current status information for this agent"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "specialization": self.specialization,
            "conversation_count": len(self.conversation_history),
            "last_activity": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
    
    def should_handoff(self, request: str, context: Dict[str, Any]) -> Optional[str]:
        """Determine if this request should be handed off to another agent"""
        # This is a simple heuristic - could be enhanced with ML
        request_lower = request.lower()
        
        # Map keywords to agents
        handoff_keywords = {
            "project_manager": ["plan", "requirement", "timeline", "manage", "coordinate", "overview"],
            "code_generator": ["code", "function", "algorithm", "backend", "api", "database"],
            "ui_designer": ["ui", "interface", "design", "frontend", "layout", "style", "component"],
            "test_writer": ["test", "testing", "validate", "check", "quality", "bug"],
            "debugger": ["debug", "fix", "error", "issue", "optimize", "performance"]
        }
        
        # Don't handoff to ourselves
        current_agent_type = self.__class__.__name__.lower().replace("agent", "")
        
        for agent_type, keywords in handoff_keywords.items():
            if agent_type != current_agent_type:
                if any(keyword in request_lower for keyword in keywords):
                    return agent_type
        
        return None
