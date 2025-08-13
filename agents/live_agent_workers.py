"""
Live AI Agent Workers with Real API Integration

Implements actual Claude, GPT-4, and Gemini workers that connect to the
event-sourced orchestration system and perform real AI tasks.
"""

import asyncio
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from uuid import uuid4
import time

# AI Service imports
from anthropic import Anthropic
from openai import OpenAI
from google import genai

from core.event_streaming import StreamEvent, EventType, EventStreamType, StreamConsumer
from schemas.artifacts import ArtifactType
from schemas.routing import ModelType, TaskType
from agents.base_agent import AgentOutput, ProcessingResult

logger = logging.getLogger(__name__)


class LiveAgentMetrics:
    """Tracks real-time metrics for live agents"""

    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.average_response_time = 0.0
        self.quality_scores = []

    def record_request(
        self,
        success: bool,
        tokens: int,
        cost: float,
        response_time: float,
        quality_score: Optional[float] = None,
    ):
        """Record metrics for a request"""
        self.total_requests += 1

        if success:
            self.successful_requests += 1
            if quality_score:
                self.quality_scores.append(quality_score)
        else:
            self.failed_requests += 1

        self.total_tokens_used += tokens
        self.total_cost += cost

        # Update average response time
        self.average_response_time = (
            self.average_response_time * (self.total_requests - 1) + response_time
        ) / self.total_requests

    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    def get_average_quality(self) -> float:
        """Calculate average quality score"""
        if not self.quality_scores:
            return 0.0
        return sum(self.quality_scores) / len(self.quality_scores)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.get_success_rate(),
            "total_tokens_used": self.total_tokens_used,
            "total_cost": self.total_cost,
            "average_response_time": self.average_response_time,
            "average_quality": self.get_average_quality(),
        }


class LiveAgentWorker(StreamConsumer):
    """Base class for live AI agent workers"""

    def __init__(
        self,
        event_bus=None,
        agent_id: str = "",
        model_type: ModelType = ModelType.CLAUDE,
    ):
        from bus import bus

        super().__init__(bus, f"{agent_id}_worker")
        self.agent_id = agent_id
        self.model_type = model_type
        self.metrics = LiveAgentMetrics()
        self.task_assignments = {}  # Track assigned tasks

    async def process_event(self, event: StreamEvent):
        """Process events from the task stream"""

        if event.event_type == EventType.TASK_CREATED:
            # New task available - evaluate if we should handle it
            await self._evaluate_task_assignment(event)

        elif (
            event.event_type == EventType.TASK_ASSIGNED
            and event.agent_id == self.agent_id
        ):
            # Task specifically assigned to this agent
            await self._execute_assigned_task(event)

    async def _evaluate_task_assignment(self, event: StreamEvent):
        """Evaluate if this agent should handle the task"""

        task_data = event.payload
        task_type = task_data.get("primary_task_type")

        # Check if this agent can handle the task type
        if self._can_handle_task_type(task_type):
            logger.info(f"{self.agent_id} can handle task {event.correlation_id}")

            # Publish interest in the task
            interest_event = StreamEvent(
                correlation_id=event.correlation_id,
                event_type=EventType.AGENT_REGISTERED,
                agent_id=self.agent_id,
                task_id=task_data.get("task_id"),
                payload={
                    "capability_match": True,
                    "confidence": self._calculate_task_confidence(task_data),
                    "estimated_cost": self._estimate_task_cost(task_data),
                    "estimated_time": self._estimate_completion_time(task_data),
                },
            )

            await self.event_bus.publish_event(
                EventStreamType.AGENT_STATUS, interest_event
            )

    async def _execute_assigned_task(self, event: StreamEvent):
        """Execute a task assigned to this agent"""

        task_data = event.payload
        task_id = task_data.get("task_id", f"task_{uuid4().hex[:8]}")

        # Record task assignment
        self.task_assignments[task_id] = {
            "start_time": datetime.now(timezone.utc),
            "correlation_id": event.correlation_id,
            "task_data": task_data,
        }

        # Publish task started event
        start_event = StreamEvent(
            correlation_id=event.correlation_id,
            event_type=EventType.TASK_STARTED,
            agent_id=self.agent_id,
            task_id=task_id,
            payload={"status": "started", "agent_type": str(self.model_type)},
        )

        await self.event_bus.publish_event(EventStreamType.TASKS, start_event)

        try:
            # Execute the actual AI task
            result = await self._execute_ai_task(task_data)

            if result.success:
                # Publish artifact created event
                artifact_event = StreamEvent(
                    correlation_id=event.correlation_id,
                    event_type=EventType.ARTIFACT_CREATED,
                    agent_id=self.agent_id,
                    task_id=task_id,
                    artifact_id=result.output.artifact["artifact_id"],
                    payload=result.output.artifact,
                    metadata={
                        "processing_time": result.processing_time,
                        "tokens_used": result.resource_usage.get("tokens_used", 0),
                        "cost": result.resource_usage.get("cost", 0.0),
                        "quality_score": result.output.quality_score,
                        "confidence": result.output.confidence,
                    },
                )

                await self.event_bus.publish_event(
                    EventStreamType.ARTIFACTS, artifact_event
                )

                # Publish task completed event
                completion_event = StreamEvent(
                    correlation_id=event.correlation_id,
                    event_type=EventType.TASK_COMPLETED,
                    agent_id=self.agent_id,
                    task_id=task_id,
                    payload={
                        "status": "completed",
                        "artifact_id": result.output.artifact["artifact_id"],
                        "quality_score": result.output.quality_score,
                    },
                )

                await self.event_bus.publish_event(
                    EventStreamType.TASKS, completion_event
                )

                # Record metrics
                self.metrics.record_request(
                    success=True,
                    tokens=result.resource_usage.get("tokens_used", 0),
                    cost=result.resource_usage.get("cost", 0.0),
                    response_time=result.processing_time,
                    quality_score=result.output.quality_score,
                )

                logger.info(f"{self.agent_id} completed task {task_id} successfully")

            else:
                # Handle task failure
                await self._handle_task_failure(
                    event.correlation_id, task_id, result.error_message
                )

        except Exception as e:
            logger.error(f"{self.agent_id} failed to execute task {task_id}: {e}")
            await self._handle_task_failure(event.correlation_id, task_id, str(e))

        finally:
            # Clean up task assignment
            if task_id in self.task_assignments:
                del self.task_assignments[task_id]

    async def _handle_task_failure(self, correlation_id: str, task_id: str, error: str):
        """Handle task execution failure"""

        failure_event = StreamEvent(
            correlation_id=correlation_id,
            event_type=EventType.TASK_FAILED,
            agent_id=self.agent_id,
            task_id=task_id,
            payload={"status": "failed", "error": error},
        )

        await self.event_bus.publish_event(EventStreamType.TASKS, failure_event)

        # Record failure metrics
        self.metrics.record_request(
            success=False, tokens=0, cost=0.0, response_time=0.0
        )

    # Abstract methods to be implemented by specific agent types
    def _can_handle_task_type(self, task_type: str) -> bool:
        """Check if this agent can handle the task type"""
        raise NotImplementedError

    def _calculate_task_confidence(self, task_data: Dict[str, Any]) -> float:
        """Calculate confidence for handling this task"""
        raise NotImplementedError

    def _estimate_task_cost(self, task_data: Dict[str, Any]) -> float:
        """Estimate cost for this task"""
        raise NotImplementedError

    def _estimate_completion_time(self, task_data: Dict[str, Any]) -> float:
        """Estimate completion time in minutes"""
        raise NotImplementedError

    async def _execute_ai_task(self, task_data: Dict[str, Any]) -> ProcessingResult:
        """Execute the actual AI task"""
        raise NotImplementedError


class ClaudeWorker(LiveAgentWorker):
    """Claude agent worker for strategic planning, architecture, and debugging"""

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus, "claude_agent", ModelType.CLAUDE_SONNET)

        # Initialize Claude client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")

        self.client = Anthropic(api_key=api_key)

        # Claude specialties
        self.primary_tasks = [
            TaskType.REASONING_LONG,
            TaskType.ARCHITECTURE,
            TaskType.DOCUMENTATION,
            TaskType.CODE_REVIEW,
        ]

        logger.info("Claude worker initialized with real API integration")

    def _can_handle_task_type(self, task_type: str) -> bool:
        """Claude specializes in complex reasoning and architecture"""
        claude_tasks = [
            "reasoning",
            "architecture",
            "documentation",
            "debugging",
            "analysis",
        ]
        return any(specialty in task_type.lower() for specialty in claude_tasks)

    def _calculate_task_confidence(self, task_data: Dict[str, Any]) -> float:
        """Claude has high confidence for reasoning and architecture tasks"""
        task_type = task_data.get("primary_task_type", "").lower()

        if "reasoning" in task_type or "architecture" in task_type:
            return 0.95
        elif "documentation" in task_type or "analysis" in task_type:
            return 0.90
        elif "debugging" in task_type or "review" in task_type:
            return 0.85
        else:
            return 0.60

    def _estimate_task_cost(self, task_data: Dict[str, Any]) -> float:
        """Estimate Claude API cost (approximate)"""
        estimated_tokens = task_data.get("estimated_tokens", 5000)
        # Claude 3 Sonnet pricing: ~$3/1M input tokens, ~$15/1M output tokens
        input_cost = estimated_tokens * 0.000003
        output_cost = estimated_tokens * 0.5 * 0.000015  # Assume 50% output ratio
        return input_cost + output_cost

    def _estimate_completion_time(self, task_data: Dict[str, Any]) -> float:
        """Estimate completion time based on task complexity"""
        complexity = task_data.get("complexity", 0.5)
        base_time = 3.0  # 3 minutes base
        return base_time * (1 + complexity)

    async def _execute_ai_task(self, task_data: Dict[str, Any]) -> ProcessingResult:
        """Execute task using Claude API"""

        start_time = time.time()

        try:
            # Prepare the task prompt
            task_prompt = self._build_task_prompt(task_data)

            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": task_prompt}],
            )

            # Extract response
            content = response.content[0].text if response.content else ""

            # Calculate metrics
            input_tokens = (
                response.usage.input_tokens if hasattr(response, "usage") else 0
            )
            output_tokens = (
                response.usage.output_tokens if hasattr(response, "usage") else 0
            )
            total_tokens = input_tokens + output_tokens

            # Estimate cost
            cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)

            processing_time = time.time() - start_time

            # Create artifact based on task type
            artifact = self._create_artifact_from_response(task_data, content)

            # Create agent output
            agent_output = AgentOutput(
                request_id=task_data.get("task_id", str(uuid4())),
                processing_duration=processing_time,
                agent_id=self.agent_id,
                model_used=self.model_type,
                artifact=artifact,
                confidence=0.85,
                quality_score=0.88,
                completeness_score=0.90,
                notes=f"Claude generated {artifact['artifact_type']} with {total_tokens} tokens",
                tokens_consumed=total_tokens,
            )

            return ProcessingResult(
                success=True,
                output=agent_output,
                processing_time=processing_time,
                resource_usage={
                    "tokens_used": total_tokens,
                    "cost": cost,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            )

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time,
            )

    def _build_task_prompt(self, task_data: Dict[str, Any]) -> str:
        """Build prompt for Claude based on task data"""

        task_type = task_data.get("primary_task_type", "general")
        objective = task_data.get(
            "objective", task_data.get("goal", "Complete the task")
        )
        context = task_data.get("context", task_data.get("description", ""))

        if "architecture" in task_type.lower():
            return f"""
As a senior software architect, design a comprehensive system architecture for the following project:

Objective: {objective}

Context: {context}

Please provide:
1. High-level system overview
2. Core components and their responsibilities
3. Key architectural decisions with rationale
4. Technology stack recommendations
5. Scalability and performance considerations

Format your response as a structured design document.
            """.strip()

        elif (
            "specification" in task_type.lower() or "requirements" in task_type.lower()
        ):
            return f"""
As a business analyst and technical writer, create detailed specifications for:

Objective: {objective}

Context: {context}

Please provide:
1. Clear objective and scope definition
2. Functional and non-functional requirements
3. Acceptance criteria for each requirement
4. Assumptions and constraints
5. Success metrics and validation criteria

Format as a comprehensive specification document.
            """.strip()

        elif "debugging" in task_type.lower() or "analysis" in task_type.lower():
            return f"""
As a senior developer, analyze and provide debugging guidance for:

Objective: {objective}

Context: {context}

Please provide:
1. Problem analysis and root cause identification
2. Step-by-step debugging approach
3. Potential solutions with trade-offs
4. Prevention strategies for similar issues
5. Testing recommendations

Format as a technical analysis report.
            """.strip()

        else:
            return f"""
As an expert developer, complete the following task:

Objective: {objective}

Context: {context}

Please provide a comprehensive solution with clear explanations and practical implementation guidance.
            """.strip()

    def _create_artifact_from_response(
        self, task_data: Dict[str, Any], content: str
    ) -> Dict[str, Any]:
        """Create structured artifact from Claude's response"""

        task_type = task_data.get("primary_task_type", "general").lower()
        artifact_id = f"claude_{task_type}_{uuid4().hex[:8]}"

        base_artifact = {
            "artifact_id": artifact_id,
            "created_by": self.agent_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.85,
            "version": "1.0.0",
            "tags": ["claude", "real-ai", task_type],
        }

        if "architecture" in task_type:
            return {
                **base_artifact,
                "artifact_type": ArtifactType.DESIGN_DOC.value,
                "title": f"System Architecture: {task_data.get('objective', 'Project')}",
                "overview": content,
                "components": [],
                "design_decisions": [],
            }

        elif "specification" in task_type or "requirements" in task_type:
            return {
                **base_artifact,
                "artifact_type": ArtifactType.SPEC_DOC.value,
                "title": f"Specification: {task_data.get('objective', 'Project')}",
                "objective": task_data.get("objective", ""),
                "requirements": [],
                "acceptance_criteria": [],
                "content": content,
            }

        else:
            return {
                **base_artifact,
                "artifact_type": ArtifactType.RUNBOOK.value,
                "title": f"Analysis: {task_data.get('objective', 'Task')}",
                "purpose": task_data.get("objective", ""),
                "content": content,
                "procedures": [],
            }


class GPT4Worker(LiveAgentWorker):
    """GPT-4 agent worker for code generation and creative solutions"""

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus, "gpt4_agent", ModelType.GPT4O)

        # Initialize OpenAI client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")

        self.client = OpenAI(api_key=api_key)

        # GPT-4 specialties
        self.primary_tasks = [
            TaskType.CODE_BACKEND,
            TaskType.CODE_UI,
            TaskType.CODE_REVIEW,
        ]

        logger.info("GPT-4 worker initialized with real API integration")

    def _can_handle_task_type(self, task_type: str) -> bool:
        """GPT-4 specializes in code generation and implementation"""
        gpt4_tasks = [
            "code",
            "implementation",
            "programming",
            "development",
            "ui",
            "frontend",
        ]
        return any(specialty in task_type.lower() for specialty in gpt4_tasks)

    def _calculate_task_confidence(self, task_data: Dict[str, Any]) -> float:
        """GPT-4 has high confidence for coding tasks"""
        task_type = task_data.get("primary_task_type", "").lower()

        if "code" in task_type or "programming" in task_type:
            return 0.92
        elif "implementation" in task_type or "development" in task_type:
            return 0.88
        elif "ui" in task_type or "frontend" in task_type:
            return 0.85
        else:
            return 0.65

    def _estimate_task_cost(self, task_data: Dict[str, Any]) -> float:
        """Estimate GPT-4 API cost"""
        estimated_tokens = task_data.get("estimated_tokens", 4000)
        # GPT-4 pricing: ~$10/1M input tokens, ~$30/1M output tokens
        input_cost = estimated_tokens * 0.00001
        output_cost = estimated_tokens * 0.6 * 0.00003  # Assume 60% output for code
        return input_cost + output_cost

    def _estimate_completion_time(self, task_data: Dict[str, Any]) -> float:
        """Estimate completion time"""
        complexity = task_data.get("complexity", 0.5)
        base_time = 4.0  # 4 minutes base for coding tasks
        return base_time * (1 + complexity * 1.5)

    async def _execute_ai_task(self, task_data: Dict[str, Any]) -> ProcessingResult:
        """Execute task using GPT-4 API"""

        start_time = time.time()

        try:
            task_prompt = self._build_code_prompt(task_data)

            # Call GPT-4 API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": task_prompt}],
                max_tokens=3000,
                temperature=0.1,  # Lower temperature for more consistent code
            )

            content = response.choices[0].message.content if response.choices else ""

            # Calculate metrics
            total_tokens = response.usage.total_tokens if response.usage else 0
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = (
                response.usage.completion_tokens if response.usage else 0
            )

            # Estimate cost (GPT-4o pricing)
            cost = (prompt_tokens * 0.000005) + (completion_tokens * 0.000015)

            processing_time = time.time() - start_time

            # Create code artifact
            artifact = self._create_code_artifact(task_data, content)

            agent_output = AgentOutput(
                request_id=task_data.get("task_id", str(uuid4())),
                processing_duration=processing_time,
                agent_id=self.agent_id,
                model_used=self.model_type,
                artifact=artifact,
                confidence=0.88,
                quality_score=0.85,
                completeness_score=0.87,
                notes=f"GPT-4 generated {artifact['artifact_type']} with {total_tokens} tokens",
                tokens_consumed=total_tokens,
            )

            return ProcessingResult(
                success=True,
                output=agent_output,
                processing_time=processing_time,
                resource_usage={
                    "tokens_used": total_tokens,
                    "cost": cost,
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens,
                },
            )

        except Exception as e:
            logger.error(f"GPT-4 API error: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time,
            )

    def _build_code_prompt(self, task_data: Dict[str, Any]) -> str:
        """Build coding prompt for GPT-4"""

        objective = task_data.get("objective", task_data.get("goal", ""))
        context = task_data.get("context", task_data.get("description", ""))
        task_data.get("primary_task_type", "code")

        return f"""
As an expert software developer, implement the following:

Objective: {objective}

Context: {context}

Requirements:
- Write clean, well-documented code
- Follow best practices and design patterns
- Include error handling where appropriate
- Provide clear comments and documentation
- Consider performance and maintainability

Please provide the complete implementation with explanations.
        """.strip()

    def _create_code_artifact(
        self, task_data: Dict[str, Any], content: str
    ) -> Dict[str, Any]:
        """Create code patch artifact from GPT-4's response"""

        artifact_id = f"gpt4_code_{uuid4().hex[:8]}"

        return {
            "artifact_id": artifact_id,
            "artifact_type": ArtifactType.CODE_PATCH.value,
            "created_by": self.agent_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.88,
            "version": "1.0.0",
            "title": f"Implementation: {task_data.get('objective', 'Code')}",
            "description": f"GPT-4 generated code for {task_data.get('objective', 'task')}",
            "files_changed": [{"path": "implementation.py", "action": "created"}],
            "diff_unified": content,
            "language": "python",
            "test_instructions": ["Run unit tests", "Verify functionality"],
            "tags": ["gpt4", "real-ai", "implementation"],
        }


class GeminiWorker(LiveAgentWorker):
    """Gemini agent worker for testing, validation, and quality assurance"""

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus, "gemini_agent", ModelType.GEMINI_FLASH)

        # Initialize Gemini client
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable required")

        self.client = genai.Client(api_key=api_key)

        # Gemini specialties
        self.primary_tasks = [
            TaskType.TEST_GEN,
            TaskType.CODE_REVIEW,
            TaskType.DOCUMENTATION,
        ]

        logger.info("Gemini worker initialized with real API integration")

    def _can_handle_task_type(self, task_type: str) -> bool:
        """Gemini specializes in testing and validation"""
        gemini_tasks = ["test", "validation", "quality", "review", "qa"]
        return any(specialty in task_type.lower() for specialty in gemini_tasks)

    def _calculate_task_confidence(self, task_data: Dict[str, Any]) -> float:
        """Gemini confidence for testing tasks"""
        task_type = task_data.get("primary_task_type", "").lower()

        if "test" in task_type or "validation" in task_type:
            return 0.90
        elif "quality" in task_type or "review" in task_type:
            return 0.86
        elif "qa" in task_type:
            return 0.88
        else:
            return 0.70

    def _estimate_task_cost(self, task_data: Dict[str, Any]) -> float:
        """Estimate Gemini API cost (very low cost)"""
        estimated_tokens = task_data.get("estimated_tokens", 3000)
        # Gemini Flash is very cost-effective
        return estimated_tokens * 0.0000005

    def _estimate_completion_time(self, task_data: Dict[str, Any]) -> float:
        """Estimate completion time (Gemini is fast)"""
        complexity = task_data.get("complexity", 0.5)
        base_time = 2.0  # 2 minutes base (fast processing)
        return base_time * (1 + complexity * 0.8)

    async def _execute_ai_task(self, task_data: Dict[str, Any]) -> ProcessingResult:
        """Execute task using Gemini API"""

        start_time = time.time()

        try:
            task_prompt = self._build_test_prompt(task_data)

            # Call Gemini API
            response = self.client.models.generate_content(
                model="gemini-1.5-flash", contents=task_prompt
            )

            content = response.text or ""

            # Gemini doesn't provide detailed token usage, so estimate
            estimated_tokens = len(task_prompt) + len(content)
            cost = estimated_tokens * 0.0000005

            processing_time = time.time() - start_time

            # Create test artifact
            artifact = self._create_test_artifact(task_data, content)

            agent_output = AgentOutput(
                request_id=task_data.get("task_id", str(uuid4())),
                processing_duration=processing_time,
                agent_id=self.agent_id,
                model_used=self.model_type,
                artifact=artifact,
                confidence=0.86,
                quality_score=0.84,
                completeness_score=0.88,
                notes=f"Gemini generated {artifact['artifact_type']} with ~{estimated_tokens} tokens",
                tokens_consumed=estimated_tokens,
            )

            return ProcessingResult(
                success=True,
                output=agent_output,
                processing_time=processing_time,
                resource_usage={"tokens_used": estimated_tokens, "cost": cost},
            )

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time,
            )

    def _build_test_prompt(self, task_data: Dict[str, Any]) -> str:
        """Build testing prompt for Gemini"""

        objective = task_data.get("objective", task_data.get("goal", ""))
        context = task_data.get("context", task_data.get("description", ""))

        return f"""
As a quality assurance engineer, create comprehensive tests for:

Objective: {objective}

Context: {context}

Please provide:
1. Test strategy and approach
2. Unit test cases with expected outcomes
3. Integration test scenarios
4. Edge cases and error conditions
5. Performance and load testing considerations
6. Test automation recommendations

Format as a detailed test plan with executable test cases.
        """.strip()

    def _create_test_artifact(
        self, task_data: Dict[str, Any], content: str
    ) -> Dict[str, Any]:
        """Create test plan artifact from Gemini's response"""

        artifact_id = f"gemini_test_{uuid4().hex[:8]}"

        return {
            "artifact_id": artifact_id,
            "artifact_type": ArtifactType.TEST_PLAN.value,
            "created_by": self.agent_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.86,
            "version": "1.0.0",
            "title": f"Test Plan: {task_data.get('objective', 'Quality Assurance')}",
            "objective": task_data.get("objective", ""),
            "test_strategy": "Comprehensive testing approach with automation",
            "test_cases": [],
            "coverage_requirements": ["Unit tests", "Integration tests", "E2E tests"],
            "tools": ["pytest", "unittest", "integration-test-framework"],
            "content": content,
            "tags": ["gemini", "real-ai", "testing"],
        }


class LiveAgentOrchestrator:
    """Orchestrator that manages live AI agent workers"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.workers: Dict[str, LiveAgentWorker] = {}
        self.task_assignments = {}
        self.running = False

        # Initialize workers if API keys are available
        self._initialize_workers()

    def _initialize_workers(self):
        """Initialize available agent workers"""

        try:
            if os.environ.get("ANTHROPIC_API_KEY"):
                self.workers["claude"] = ClaudeWorker(self.event_bus)
                logger.info("Claude worker available")
        except Exception as e:
            logger.warning(f"Could not initialize Claude worker: {e}")

        try:
            if os.environ.get("OPENAI_API_KEY"):
                self.workers["gpt4"] = GPT4Worker(self.event_bus)
                logger.info("GPT-4 worker available")
        except Exception as e:
            logger.warning(f"Could not initialize GPT-4 worker: {e}")

        try:
            if os.environ.get("GEMINI_API_KEY"):
                self.workers["gemini"] = GeminiWorker(self.event_bus)
                logger.info("Gemini worker available")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini worker: {e}")

        logger.info(f"Initialized {len(self.workers)} live agent workers")

    async def start_workers(self):
        """Start all agent workers"""

        if not self.workers:
            logger.warning("No agent workers available - check API keys")
            return

        self.running = True

        # Start each worker as a consumer
        worker_tasks = []
        for worker_name, worker in self.workers.items():
            task = asyncio.create_task(
                worker.start(EventStreamType.TASKS, "live_agents_group")
            )
            worker_tasks.append(task)
            logger.info(f"Started {worker_name} worker")

        # Wait for all workers to complete (they run indefinitely)
        try:
            await asyncio.gather(*worker_tasks)
        except Exception as e:
            logger.error(f"Worker error: {e}")

    def stop_workers(self):
        """Stop all agent workers"""

        self.running = False

        for worker_name, worker in self.workers.items():
            worker.stop()
            logger.info(f"Stopped {worker_name} worker")

    def get_worker_metrics(self) -> Dict[str, Any]:
        """Get metrics from all workers"""

        metrics = {}
        for worker_name, worker in self.workers.items():
            metrics[worker_name] = {
                "agent_id": worker.agent_id,
                "model_type": str(worker.model_type),
                "metrics": worker.metrics.to_dict(),
                "active_tasks": len(worker.task_assignments),
                "running": worker.running,
            }

        return {
            "total_workers": len(self.workers),
            "active_workers": sum(1 for w in self.workers.values() if w.running),
            "worker_details": metrics,
        }

    async def assign_task_to_best_agent(
        self, task_data: Dict[str, Any], correlation_id: str
    ) -> Optional[str]:
        """Intelligently assign task to the best available agent"""

        if not self.workers:
            logger.warning("No workers available for task assignment")
            return None

        # Evaluate each worker's capability for this task
        candidates = []

        for worker_name, worker in self.workers.items():
            if worker._can_handle_task_type(task_data.get("primary_task_type", "")):
                confidence = worker._calculate_task_confidence(task_data)
                cost = worker._estimate_task_cost(task_data)
                time_est = worker._estimate_completion_time(task_data)

                # Multi-objective scoring: quality - λ·cost - μ·latency
                score = (
                    confidence - (0.1 * cost) - (0.05 * time_est / 60)
                )  # Convert time to hours

                candidates.append(
                    {
                        "worker_name": worker_name,
                        "worker": worker,
                        "confidence": confidence,
                        "cost": cost,
                        "time_estimate": time_est,
                        "score": score,
                    }
                )

        if not candidates:
            logger.warning("No suitable workers found for task")
            return None

        # Select best candidate
        best_candidate = max(candidates, key=lambda c: c["score"])
        selected_worker = best_candidate["worker"]

        logger.info(
            f"Assigned task to {best_candidate['worker_name']} with score {best_candidate['score']:.3f}"
        )

        # Publish task assignment event
        assignment_event = StreamEvent(
            correlation_id=correlation_id,
            event_type=EventType.TASK_ASSIGNED,
            agent_id=selected_worker.agent_id,
            task_id=task_data.get("task_id"),
            payload=task_data,
            metadata={
                "assignment_reason": f"Best score: {best_candidate['score']:.3f}",
                "confidence": best_candidate["confidence"],
                "estimated_cost": best_candidate["cost"],
                "estimated_time": best_candidate["time_estimate"],
            },
        )

        await self.event_bus.publish_event(EventStreamType.TASKS, assignment_event)

        return selected_worker.agent_id
