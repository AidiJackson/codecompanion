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
    
    async def call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7, task_context: str = "") -> str:
        """Make a call to the optimal AI model through orchestrator"""
        try:
            # Get optimal model for this agent type
            model_name = orchestrator.get_optimal_model(self.agent_type, task_context)
            
            # Generate response using the orchestrator
            response = await orchestrator.generate_response(
                model_name=model_name,
                messages=messages,
                agent_type=self.agent_type,
                task_id=f"{self.agent_id}_{int(datetime.now().timestamp())}"
            )
            
            return response["content"]
            
        except Exception as e:
            return f"Error communicating with AI model: {str(e)}. Please check your API keys."
    
    def call_llm_sync(self, messages: List[Dict[str, str]], temperature: float = 0.7, task_context: str = "") -> str:
        """Synchronous version of call_llm for compatibility"""
        try:
            return asyncio.run(self.call_llm(messages, temperature, task_context))
        except Exception as e:
            return f"Error communicating with AI model: {str(e)}"
    
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

    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a request with real API calls to AI models"""
        context = context or {}
        
        try:
            # Get health checker and working client
            from core.api_health_checker import APIHealthChecker
            health_checker = APIHealthChecker()
            health_checker.initialize_clients()
            
            # Map agent model preferences
            service_mapping = {
                "PROJECT_MANAGER": "anthropic",  # Use Claude for planning
                "CODE_GENERATOR": "openai",      # Use GPT-4 for coding  
                "UI_DESIGNER": "openai",         # Use GPT-4 for design
                "TEST_WRITER": "google",         # Use Gemini for testing
                "DEBUGGER": "anthropic"          # Use Claude for debugging
            }
            
            service = service_mapping.get(self.agent_type, "openai")
            client = health_checker.get_working_client(service)
            
            if not client:
                return {
                    "content": f"[{self.name}] AI model not available. Please test API connections in the dashboard.",
                    "files": {},
                    "error": f"Service {service} connection failed"
                }
            
            # Create agent-specific system prompt
            system_prompt = f"{self.get_system_prompt()}"
            if context.get('project_context'):
                system_prompt += f"\n\nProject Context: {context['project_context']}"
            
            # Make actual API call based on service
            if service == "openai":
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": request}
                    ],
                    max_tokens=1500,
                    temperature=0.7
                )
                content = response.choices[0].message.content
                
            elif service == "anthropic":
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1500,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[{"role": "user", "content": request}]
                )
                content = response.content[0].text if response.content else "No response"
                
            elif service == "google":
                full_prompt = f"{system_prompt}\n\nUser request: {request}"
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt
                )
                content = response.text if response.text else "No response"
            
            else:
                content = f"[{self.name}] Service {service} not supported"
            
            # Process the response
            processed_response = {
                "content": content,
                "files": {},
                "metadata": {
                    "agent": self.name,
                    "agent_type": self.agent_type,
                    "service_used": service,
                    "timestamp": datetime.now().isoformat(),
                    "request_length": len(request)
                }
            }
            
            # Add to history
            self.add_to_history(request, content)
            
            # Check if handoff is needed
            handoff_target = self.should_handoff(request, context)
            if handoff_target:
                processed_response["handoff_suggestion"] = handoff_target
            
            return processed_response
            
        except Exception as e:
            error_response = {
                "content": f"[{self.name}] Error processing request: {str(e)}",
                "files": {},
                "error": str(e),
                "metadata": {
                    "agent": self.name,
                    "timestamp": datetime.now().isoformat(),
                    "error_type": type(e).__name__
                }
            }
            
            self.add_to_history(request, f"Error: {str(e)}")
            return error_response
