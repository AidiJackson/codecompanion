from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import os
from openai import OpenAI

class BaseAgent(ABC):
    """Base class for all AI agents in the multi-agent system"""
    
    def __init__(self, name: str, role: str, specialization: str):
        self.name = name
        self.role = role
        self.specialization = specialization
        self.agent_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now()
        self.conversation_history: List[Dict] = []
        
        # Initialize OpenAI client
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.openai_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", "your-openai-api-key")
        )
        self.model = "gpt-4o"
    
    @abstractmethod
    def process_request(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a user request and return response with potential handoffs"""
        pass
    
    @abstractmethod
    def process_handoff(self, handoff_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Make a call to the language model"""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with AI model: {str(e)}. Please check your OpenAI API key."
    
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
