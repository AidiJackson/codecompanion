"""
Multi-Model AI Orchestration System
Manages Claude, GPT-4, and Gemini APIs for specialized agent tasks
"""

import os
import time
import asyncio
from typing import Dict, List, Any
from enum import Enum
from datetime import datetime
import streamlit as st

# Import AI clients
try:
    import openai
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from google import genai

    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False


class AIModel(Enum):
    """Supported AI models"""

    GPT4 = "gpt-4o"  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
    CLAUDE = "claude-sonnet-4-20250514"  # The newest Anthropic model is "claude-sonnet-4-20250514", not "claude-3-5-sonnet-20241022" nor "claude-3-sonnet-20240229"
    GEMINI = "gemini-2.5-flash"  # Note that the newest Gemini model series is "gemini-2.5-flash"


class AgentType(Enum):
    """Agent specializations mapped to optimal models"""

    PROJECT_MANAGER = ("claude", "Strategic planning and architecture decisions")
    CODE_GENERATOR = ("gpt4", "Creative coding and problem-solving")
    UI_DESIGNER = ("gpt4", "Design creativity and user experience")
    TEST_WRITER = ("gemini", "Systematic testing and validation")
    DEBUGGER = ("claude", "Logical problem-solving and analysis")


class ModelStatus:
    """Track model connection status and performance"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.is_connected = False
        self.last_used = None
        self.response_times = []
        self.error_count = 0
        self.success_count = 0

    def record_success(self, response_time: float):
        self.last_used = datetime.now()
        self.response_times.append(response_time)
        if len(self.response_times) > 10:  # Keep only last 10 response times
            self.response_times.pop(0)
        self.success_count += 1

    def record_error(self):
        self.error_count += 1

    @property
    def avg_response_time(self) -> float:
        return (
            sum(self.response_times) / len(self.response_times)
            if self.response_times
            else 0
        )

    @property
    def reliability(self) -> float:
        total = self.success_count + self.error_count
        return self.success_count / total if total > 0 else 0


class ModelOrchestrator:
    """Orchestrates multiple AI models for collaborative development"""

    def __init__(self):
        self.clients = {}
        self.model_status = {
            "gpt4": ModelStatus("GPT-4"),
            "claude": ModelStatus("Claude"),
            "gemini": ModelStatus("Gemini"),
        }
        self.active_tasks = {}
        self.consensus_sessions = {}

        # Initialize clients
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize AI clients based on available API keys"""
        # OpenAI GPT-4
        if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
            try:
                self.clients["gpt4"] = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                self.model_status["gpt4"].is_connected = True
            except Exception as e:
                st.error(f"Failed to initialize OpenAI client: {e}")

        # Anthropic Claude
        if ANTHROPIC_AVAILABLE and os.environ.get("ANTHROPIC_API_KEY"):
            try:
                self.clients["claude"] = Anthropic(
                    api_key=os.environ.get("ANTHROPIC_API_KEY")
                )
                self.model_status["claude"].is_connected = True
            except Exception as e:
                st.error(f"Failed to initialize Anthropic client: {e}")

        # Google Gemini
        if GOOGLE_GENAI_AVAILABLE and os.environ.get("GEMINI_API_KEY"):
            try:
                self.clients["gemini"] = genai.Client(
                    api_key=os.environ.get("GEMINI_API_KEY")
                )
                self.model_status["gemini"].is_connected = True
            except Exception as e:
                st.error(f"Failed to initialize Gemini client: {e}")

    def test_connections(self) -> Dict[str, bool]:
        """Test connections to all configured models"""
        results = {}

        for model_name, client in self.clients.items():
            try:
                if model_name == "gpt4":
                    response = client.chat.completions.create(
                        model=AIModel.GPT4.value,
                        messages=[
                            {
                                "role": "user",
                                "content": "Test connection. Reply with 'OK'.",
                            }
                        ],
                        max_tokens=10,
                    )
                    results[model_name] = "OK" in response.choices[0].message.content

                elif model_name == "claude":
                    response = client.messages.create(
                        model=AIModel.CLAUDE.value,
                        max_tokens=10,
                        messages=[
                            {
                                "role": "user",
                                "content": "Test connection. Reply with 'OK'.",
                            }
                        ],
                    )
                    results[model_name] = "OK" in response.content[0].text

                elif model_name == "gemini":
                    response = client.models.generate_content(
                        model=AIModel.GEMINI.value,
                        contents="Test connection. Reply with 'OK'.",
                    )
                    results[model_name] = "OK" in (response.text or "")

                if results.get(model_name, False):
                    self.model_status[model_name].is_connected = True

            except Exception:
                results[model_name] = False
                self.model_status[model_name].record_error()

        return results

    def get_optimal_model(self, agent_type: AgentType, task_context: str = "") -> str:
        """Get the optimal model for an agent type with fallback logic"""
        preferred_model = agent_type.value[0]

        # Check if preferred model is available
        if (
            preferred_model in self.clients
            and self.model_status[preferred_model].is_connected
        ):
            return preferred_model

        # Fallback logic based on task context
        available_models = [
            name
            for name, status in self.model_status.items()
            if status.is_connected and name in self.clients
        ]

        if not available_models:
            raise Exception("No AI models are currently available")

        # Choose most reliable available model
        best_model = max(
            available_models, key=lambda x: self.model_status[x].reliability
        )
        return best_model

    async def generate_response(
        self,
        model_name: str,
        messages: List[Dict],
        agent_type: AgentType,
        task_id: str = None,
    ) -> Dict[str, Any]:
        """Generate response from specified model with tracking"""
        start_time = time.time()
        task_id = task_id or f"task_{int(time.time())}"

        # Track active task
        self.active_tasks[task_id] = {
            "model": model_name,
            "agent_type": agent_type.name,
            "start_time": start_time,
            "status": "processing",
        }

        try:
            client = self.clients[model_name]
            response_content = ""

            if model_name == "gpt4":
                response = client.chat.completions.create(
                    model=AIModel.GPT4.value,
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.7,
                )
                response_content = response.choices[0].message.content

            elif model_name == "claude":
                # Convert messages format for Claude
                claude_messages = []
                system_prompt = ""

                for msg in messages:
                    if msg["role"] == "system":
                        system_prompt = msg["content"]
                    else:
                        claude_messages.append(msg)

                response = client.messages.create(
                    model=AIModel.CLAUDE.value,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=claude_messages,
                )
                response_content = response.content[0].text

            elif model_name == "gemini":
                # Convert messages to Gemini format
                prompt = "\n".join(
                    [f"{msg['role']}: {msg['content']}" for msg in messages]
                )
                response = client.models.generate_content(
                    model=AIModel.GEMINI.value, contents=prompt
                )
                response_content = response.text or ""

            # Record success
            response_time = time.time() - start_time
            self.model_status[model_name].record_success(response_time)

            # Update task status
            self.active_tasks[task_id].update(
                {
                    "status": "completed",
                    "response_time": response_time,
                    "response_length": len(response_content),
                }
            )

            return {
                "content": response_content,
                "model": model_name,
                "agent_type": agent_type.name,
                "response_time": response_time,
                "task_id": task_id,
            }

        except Exception as e:
            self.model_status[model_name].record_error()
            self.active_tasks[task_id].update({"status": "failed", "error": str(e)})
            raise e

        finally:
            # Clean up old tasks
            if len(self.active_tasks) > 100:
                oldest_tasks = sorted(
                    self.active_tasks.items(), key=lambda x: x[1]["start_time"]
                )[:50]
                for task_id, _ in oldest_tasks:
                    del self.active_tasks[task_id]

    async def multi_model_consensus(
        self, question: str, models: List[str] = None, consensus_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """Get consensus from multiple models on a complex decision"""
        if models is None:
            models = [
                name
                for name, status in self.model_status.items()
                if status.is_connected and name in self.clients
            ]

        consensus_id = f"consensus_{int(time.time())}"
        self.consensus_sessions[consensus_id] = {
            "question": question,
            "models": models,
            "responses": {},
            "start_time": time.time(),
            "status": "processing",
        }

        messages = [
            {
                "role": "system",
                "content": "Provide a clear, concise answer to the following question. Focus on the key decision factors.",
            },
            {"role": "user", "content": question},
        ]

        # Get responses from all models
        responses = {}
        tasks = []

        for model in models:
            if model in self.clients:
                task = self.generate_response(
                    model,
                    messages,
                    AgentType.PROJECT_MANAGER,
                    f"{consensus_id}_{model}",
                )
                tasks.append(task)

        # Wait for all responses
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        valid_responses = []
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                model_name = models[i] if i < len(models) else f"model_{i}"
                responses[model_name] = result["content"]
                valid_responses.append(result["content"])

        # Simple consensus analysis (could be enhanced with NLP)
        consensus_score = len(valid_responses) / len(models) if models else 0

        self.consensus_sessions[consensus_id].update(
            {
                "responses": responses,
                "consensus_score": consensus_score,
                "status": "completed",
                "duration": time.time()
                - self.consensus_sessions[consensus_id]["start_time"],
            }
        )

        return {
            "consensus_id": consensus_id,
            "responses": responses,
            "consensus_score": consensus_score,
            "recommendation": valid_responses[0]
            if valid_responses
            else "No valid responses received",
            "model_count": len(valid_responses),
        }

    def get_model_statistics(self) -> Dict[str, Dict]:
        """Get performance statistics for all models"""
        stats = {}
        for name, status in self.model_status.items():
            stats[name] = {
                "is_connected": status.is_connected,
                "avg_response_time": round(status.avg_response_time, 2),
                "reliability": round(status.reliability * 100, 1),
                "success_count": status.success_count,
                "error_count": status.error_count,
                "last_used": status.last_used.isoformat() if status.last_used else None,
            }
        return stats

    def get_active_tasks(self) -> Dict[str, Dict]:
        """Get currently active tasks"""
        return self.active_tasks.copy()

    def get_recent_consensus_sessions(self, limit: int = 5) -> List[Dict]:
        """Get recent consensus sessions"""
        sessions = sorted(
            self.consensus_sessions.items(),
            key=lambda x: x[1]["start_time"],
            reverse=True,
        )
        return [{"id": sid, **data} for sid, data in sessions[:limit]]


# Global orchestrator instance
orchestrator = ModelOrchestrator()


def reinitialize_orchestrator():
    """Reinitialize the orchestrator (call when API keys change)"""
    global orchestrator
    orchestrator = ModelOrchestrator()
    return orchestrator
