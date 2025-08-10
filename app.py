"""
CodeCompanion Orchestra v3 - Comprehensive JSON Schema-based Multi-Agent System

Demonstrates the complete artifact-driven communication system with:
- Event-sourced orchestration 
- Data-driven model routing
- Structured artifact validation
- Agent I/O contracts
- Real-time workflow monitoring
"""

import streamlit as st
import asyncio
import json
import requests
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import threading
import time

# Schema imports
from schemas.artifacts import ArtifactType, SpecDoc, DesignDoc, CodePatch, TestPlan, EvalReport, Runbook
from schemas.ledgers import TaskLedger, ProgressLedger, WorkItem, TaskStatus, Priority
from schemas.routing import ModelType, TaskType, TaskComplexity, ModelRouter, MODEL_CAPABILITIES

# Core system imports  
from core.orchestrator import EventSourcedOrchestrator, EventType, WorkflowEvent
from core.router import DataDrivenRouter, RoutingContext
from core.artifacts import ArtifactValidator, ArtifactHandler
from core.event_streaming import RealTimeEventOrchestrator, EventBus, StreamEvent, EventType as StreamEventType, EventStreamType

# Agent imports
from agents.base_agent import BaseAgent, AgentInput, AgentOutput, AgentCapability, AgentType


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit configuration
st.set_page_config(
    page_title="CodeCompanion Orchestra v3",
    page_icon="🎼",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Initialize session state with system components"""
    
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = EventSourcedOrchestrator("workflow_001")
    
    if 'router' not in st.session_state:
        st.session_state.router = DataDrivenRouter()
    
    if 'artifact_handler' not in st.session_state:
        st.session_state.artifact_handler = ArtifactHandler()
    
    if 'active_workflow' not in st.session_state:
        st.session_state.active_workflow = None
        
    if 'demo_data' not in st.session_state:
        st.session_state.demo_data = create_demo_data()
    
    if 'real_time_orchestrator' not in st.session_state:
        try:
            st.session_state.real_time_orchestrator = RealTimeEventOrchestrator("streamlit_workflow")
        except:
            st.session_state.real_time_orchestrator = None
    
    if 'api_connected' not in st.session_state:
        st.session_state.api_connected = check_api_connection()
    
    if 'event_stream' not in st.session_state:
        st.session_state.event_stream = []

def create_demo_data() -> Dict[str, Any]:
    """Create demonstration data showing the schema system"""
    
    # Example task ledger
    task = TaskLedger(
        task_id="task_api_development",
        title="Build E-commerce API",
        goal="Create comprehensive REST API for e-commerce platform",
        description="Build scalable API with product catalog, user management, and order processing",
        acceptance_tests=[
            {
                "test_id": "test_001",
                "description": "All endpoints respond with proper HTTP status codes",
                "criteria": "200 for successful requests, 404 for not found, 500 for server errors"
            },
            {
                "test_id": "test_002", 
                "description": "API documentation is auto-generated and complete",
                "criteria": "OpenAPI 3.0 spec covers all endpoints with examples"
            }
        ],
        success_criteria=[
            "All tests pass with 95% coverage",
            "API responds within 200ms for 95th percentile",
            "Comprehensive documentation available"
        ],
        assumptions=[
            "PostgreSQL database is available",
            "Redis for caching is configured",
            "Authentication service is external"
        ],
        risks=[
            {
                "risk_id": "risk_001",
                "description": "Database performance issues with large product catalogs",
                "probability": 0.3,
                "impact": "high"
            }
        ],
        expected_artifacts=[ArtifactType.SPEC_DOC, ArtifactType.DESIGN_DOC, ArtifactType.CODE_PATCH]
    )
    
    # Example artifacts
    spec_doc = SpecDoc(
        artifact_id="spec_ecommerce_api",
        created_by="claude_agent",
        title="E-commerce API Specification",
        objective="Define comprehensive API for e-commerce platform",
        requirements=[
            {
                "id": "REQ_001",
                "description": "Product catalog management with CRUD operations",
                "priority": "high",
                "category": "functional"
            },
            {
                "id": "REQ_002",
                "description": "User authentication and authorization",
                "priority": "high", 
                "category": "security"
            }
        ],
        acceptance_criteria=[
            "All endpoints documented with OpenAPI spec",
            "Rate limiting implemented (1000 requests/hour per user)",
            "Input validation on all endpoints"
        ]
    )
    
    design_doc = DesignDoc(
        artifact_id="design_ecommerce_api",
        created_by="gpt4_agent",
        dependencies=["spec_ecommerce_api"],
        title="E-commerce API Architecture",
        overview="Microservices architecture with API Gateway and event-driven updates",
        components=[
            {
                "id": "api_gateway",
                "name": "API Gateway", 
                "description": "Request routing, authentication, rate limiting",
                "technology": "FastAPI",
                "interfaces": ["HTTP REST", "WebSocket"]
            }
        ],
        design_decisions=[
            {
                "id": "decision_db",
                "name": "Database Technology",
                "description": "PostgreSQL for ACID compliance and complex queries",
                "alternatives": ["MongoDB", "MySQL"],
                "rationale": "Strong consistency required for financial transactions"
            }
        ]
    )
    
    # Example task complexity
    complexity = TaskComplexity(
        technical_complexity=0.8,
        novelty=0.6,
        safety_risk=0.4,
        context_requirement=0.7,
        interdependence=0.5,
        estimated_tokens=8000,
        requires_reasoning=True,
        requires_creativity=False,
        time_sensitive=False
    )
    
    return {
        "task": task,
        "artifacts": {
            "spec_doc": spec_doc,
            "design_doc": design_doc
        },
        "complexity": complexity
    }

def main():
    """Main application interface"""
    
    init_session_state()
    
    st.title("🎼 CodeCompanion Orchestra v3")
    st.markdown("**Comprehensive JSON Schema-based Multi-Agent AI Development System**")
    
    # API Status indicator
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        api_status = "🟢 Connected" if st.session_state.api_connected else "🔴 Disconnected"
        st.markdown(f"**API Status**: {api_status}")
    with col2:
        redis_status = "🟢 Available" if st.session_state.real_time_orchestrator and st.session_state.real_time_orchestrator.event_bus.redis else "🟡 Mock Mode"
        st.markdown(f"**Event Streaming**: {redis_status}")
    with col3:
        event_count = len(st.session_state.event_stream)
        st.markdown(f"**Live Events**: {event_count}")

    # Main navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Schema Demonstration",
        "🎯 Task & Artifact Management", 
        "🤖 Agent Orchestration",
        "📊 Routing & Performance",
        "⚡ Live Workflow Monitor",
        "🌊 Event Streaming (New)"
    ])
    
    with tab1:
        render_schema_demo()
    
    with tab2:
        render_task_management()
    
    with tab3:
        render_agent_orchestration()
        
    with tab4:
        render_routing_dashboard()
    
    with tab5:
        render_workflow_monitor()
    
    with tab6:
        render_event_streaming_dashboard()
        
    # Also add live AI agents tab
    st.markdown("---")
    if st.button("🚀 Launch Live AI Project", help="Start a real project with Claude, GPT-4, and Gemini"):
        render_live_ai_project_launcher()

def render_schema_demo():
    """Demonstrate the comprehensive schema system"""
    
    st.header("📋 Schema System Demonstration")
    st.markdown("Explore the complete JSON Schema framework with Pydantic validation")
    
    # Schema type selector
    schema_type = st.selectbox(
        "Select Schema Type to Explore:",
        options=[
            "Artifacts", "Task Ledgers", "Progress Tracking", 
            "Model Routing", "Agent I/O Contracts"
        ]
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Schema Structure")
        
        if schema_type == "Artifacts":
            st.markdown("### Available Artifact Types")
            for artifact_type in ArtifactType:
                st.markdown(f"- **{artifact_type.value}**: {get_artifact_description(artifact_type)}")
            
            # Show example artifact
            st.markdown("### Example: SpecDoc Schema")
            example_spec = st.session_state.demo_data["artifacts"]["spec_doc"]
            st.json(example_spec.model_dump())
            
        elif schema_type == "Task Ledgers":
            st.markdown("### Task Ledger Components")
            st.markdown("""
            - **Goal & Description**: Clear objective definition
            - **Acceptance Tests**: Automated validation criteria
            - **Risk Management**: Identified risks and mitigation strategies
            - **Dependencies**: Task and artifact dependencies
            - **Progress Tracking**: Real-time completion status
            """)
            
            example_task = st.session_state.demo_data["task"]
            st.json(example_task.model_dump())
            
        elif schema_type == "Model Routing":
            st.markdown("### Routing Decision Framework")
            st.markdown("""
            - **Capability Vectors**: Model performance across task types
            - **Multi-objective Optimization**: Quality, cost, latency balance
            - **Load Balancing**: Dynamic resource allocation
            - **Failure Recovery**: Automatic fallback strategies
            """)
            
            # Show model capabilities
            for model_capability in MODEL_CAPABILITIES[:2]:
                st.markdown(f"**{model_capability.display_name}**")
                st.json(model_capability.model_dump())
                break
    
    with col2:
        st.subheader("✅ Validation & Quality")
        
        # Artifact validation demonstration
        if st.button("Validate Demo Artifacts"):
            validator = ArtifactValidator()
            
            for artifact_name, artifact in st.session_state.demo_data["artifacts"].items():
                validation_result = validator.validate_artifact(artifact.dict())
                
                status = "✅ Valid" if validation_result.is_valid else "❌ Invalid"
                st.markdown(f"**{artifact_name}**: {status}")
                st.markdown(f"- Quality Score: {validation_result.quality_score:.2f}")
                st.markdown(f"- Completeness: {validation_result.completeness_score:.2f}")
                
                if validation_result.validation_errors:
                    st.error("Validation Errors:")
                    for error in validation_result.validation_errors:
                        st.markdown(f"  - {error}")
                
                if validation_result.validation_warnings:
                    st.warning("Warnings:")
                    for warning in validation_result.validation_warnings:
                        st.markdown(f"  - {warning}")
        
        # Schema statistics
        st.subheader("📊 Schema Statistics")
        stats = st.session_state.artifact_handler.get_artifact_stats()
        st.json(stats)

def render_task_management():
    """Task and artifact management interface"""
    
    st.header("🎯 Task & Artifact Management")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Current Tasks")
        
        # Display demo task
        demo_task = st.session_state.demo_data["task"]
        
        with st.expander(f"Task: {demo_task.title}", expanded=True):
            st.markdown(f"**Goal**: {demo_task.goal}")
            st.markdown(f"**Status**: {demo_task.status.value}")
            st.markdown(f"**Priority**: {demo_task.priority.value}")
            
            # Progress calculation
            progress = demo_task.calculate_progress()
            st.progress(progress / 100)
            st.caption(f"Progress: {progress:.1f}%")
            
            # Acceptance tests
            st.markdown("**Acceptance Tests:**")
            for test in demo_task.acceptance_tests:
                st.markdown(f"- {test['description']}")
            
            # Risks
            if demo_task.risks:
                st.markdown("**Identified Risks:**")
                for risk in demo_task.risks:
                    risk_level = "🔴" if risk['impact'] == "high" else "🟡"
                    st.markdown(f"{risk_level} {risk['description']} (P: {risk['probability']})")
        
        # Work item management
        st.subheader("📝 Work Items")
        if st.button("Add Work Item"):
            new_item = WorkItem(
                item_id=f"item_{len(demo_task.work_items) + 1:03d}",
                title=f"Implementation Task {len(demo_task.work_items) + 1}",
                description="New work item created",
                status=TaskStatus.PENDING,
                priority=Priority.MEDIUM
            )
            demo_task.work_items.append(new_item)
            st.rerun()
        
        for item in demo_task.work_items:
            status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}.get(item.status.value, "❓")
            st.markdown(f"{status_emoji} **{item.title}** ({item.status.value})")
    
    with col2:
        st.subheader("📄 Artifact Repository")
        
        # Artifact creation
        artifact_type = st.selectbox(
            "Create New Artifact:",
            options=[at.value for at in ArtifactType]
        )
        
        if st.button("Generate Artifact Template"):
            template = create_artifact_template(ArtifactType(artifact_type))
            st.json(template)
            
            if st.button("Store Artifact"):
                validation_result = st.session_state.artifact_handler.store_artifact(template)
                if validation_result.is_valid:
                    st.success(f"Artifact stored successfully! Quality: {validation_result.quality_score:.2f}")
                else:
                    st.error(f"Validation failed: {validation_result.validation_errors}")
        
        # Display stored artifacts
        st.subheader("📦 Stored Artifacts")
        for artifact_name, artifact in st.session_state.demo_data["artifacts"].items():
            with st.expander(f"{artifact.artifact_type}: {artifact.artifact_id}"):
                st.markdown(f"**Created by**: {artifact.created_by}")
                st.markdown(f"**Confidence**: {artifact.confidence:.2f}")
                st.markdown(f"**Version**: {artifact.version}")
                
                if st.button(f"View {artifact_name}", key=f"view_{artifact_name}"):
                    st.json(artifact.model_dump())

def render_agent_orchestration():
    """Agent orchestration and workflow management"""
    
    st.header("🤖 Agent Orchestration System")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎭 Agent Capabilities")
        
        # Mock agent capabilities
        agent_capabilities = [
            AgentCapability(
                agent_type=AgentType.PROJECT_MANAGER,
                model_type=ModelType.CLAUDE_SONNET,
                primary_tasks=[TaskType.REASONING_LONG, TaskType.ARCHITECTURE],
                produces_artifacts=[ArtifactType.SPEC_DOC, ArtifactType.DESIGN_DOC],
                avg_processing_time_minutes=5.0,
                quality_score=0.92,
                reliability_score=0.98,
                max_context_length=200000
            ),
            AgentCapability(
                agent_type=AgentType.CODE_GENERATOR,
                model_type=ModelType.GPT4O,
                primary_tasks=[TaskType.CODE_BACKEND, TaskType.CODE_UI],
                produces_artifacts=[ArtifactType.CODE_PATCH],
                avg_processing_time_minutes=8.0,
                quality_score=0.88,
                reliability_score=0.95,
                max_context_length=128000
            ),
            AgentCapability(
                agent_type=AgentType.TEST_WRITER,
                model_type=ModelType.GEMINI_FLASH,
                primary_tasks=[TaskType.TEST_GEN],
                produces_artifacts=[ArtifactType.TEST_PLAN],
                avg_processing_time_minutes=4.0,
                quality_score=0.85,
                reliability_score=0.96,
                max_context_length=1000000
            )
        ]
        
        for capability in agent_capabilities:
            # Handle both enum values and strings safely
            if hasattr(capability.agent_type, 'value'):
                agent_type_str = capability.agent_type.value
            else:
                agent_type_str = str(capability.agent_type)
                
            if hasattr(capability.model_type, 'value'):
                model_type_str = capability.model_type.value
            else:
                model_type_str = str(capability.model_type)
            
            with st.expander(f"{agent_type_str} ({model_type_str})"):
                primary_tasks_str = [task.value if hasattr(task, 'value') else str(task) for task in capability.primary_tasks]
                produces_str = [art.value if hasattr(art, 'value') else str(art) for art in capability.produces_artifacts]
                
                st.markdown(f"**Primary Tasks**: {primary_tasks_str}")
                st.markdown(f"**Produces**: {produces_str}")
                st.markdown(f"**Quality Score**: {capability.quality_score:.2f}")
                st.markdown(f"**Avg Processing**: {capability.avg_processing_time_minutes:.1f} minutes")
        
        # Agent I/O Contract Demo
        st.subheader("📋 Agent I/O Contract")
        if st.button("Create Sample Agent Input"):
            agent_input = AgentInput(
                task_id="task_api_development",
                objective="Create API specification document",
                context="E-commerce platform needs comprehensive REST API for product catalog and user management",
                requested_artifact=ArtifactType.SPEC_DOC,
                quality_threshold=0.9,
                submitted_by="orchestrator"
            )
            st.json(agent_input.model_dump())
    
    with col2:
        st.subheader("🔄 Workflow Events")
        
        orchestrator = st.session_state.orchestrator
        
        # Event stream display
        if orchestrator.events:
            st.markdown("### Recent Workflow Events")
            for event in orchestrator.events[-5:]:  # Show last 5 events
                event_icon = {
                    EventType.WORKFLOW_STARTED: "🚀",
                    EventType.TASK_CREATED: "📋",
                    EventType.TASK_ASSIGNED: "👤",
                    EventType.TASK_COMPLETED: "✅",
                    EventType.ARTIFACT_PRODUCED: "📄"
                }.get(event.event_type, "📝")
                
                st.markdown(f"{event_icon} **{event.event_type.value}** - {event.timestamp.strftime('%H:%M:%S')}")
                if event.data:
                    st.json(event.data, expanded=False)
        else:
            st.info("No workflow events yet. Start a workflow to see events here.")
        
        # Workflow controls
        st.subheader("🎮 Workflow Controls")
        
        if st.button("Start Demo Workflow"):
            # Create demo workflow
            demo_task = st.session_state.demo_data["task"]
            correlation_id = orchestrator.start_workflow([demo_task])
            
            # Simulate some workflow events
            orchestrator.assign_task(
                demo_task.task_id, 
                "claude_agent", 
                st.session_state.router.route_task(
                    demo_task, 
                    "workflow_001"
                ).routing_decision
            )
            
            orchestrator.start_task(demo_task.task_id, "claude_agent")
            
            st.success(f"Workflow started! Correlation ID: {correlation_id}")
            st.rerun()
        
        # Workflow status
        status = orchestrator.get_workflow_status()
        st.json(status)

def render_routing_dashboard():
    """Model routing and performance dashboard"""
    
    st.header("📊 Routing & Performance Dashboard")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎯 Model Routing Demo")
        
        # Task complexity input
        st.markdown("### Task Complexity Assessment")
        
        technical_complexity = st.slider("Technical Complexity", 0.0, 1.0, 0.8)
        novelty = st.slider("Novelty", 0.0, 1.0, 0.6) 
        safety_risk = st.slider("Safety Risk", 0.0, 1.0, 0.3)
        
        complexity = TaskComplexity(
            technical_complexity=technical_complexity,
            novelty=novelty,
            safety_risk=safety_risk,
            context_requirement=0.7,
            interdependence=0.5,
            estimated_tokens=5000,
            requires_reasoning=True,
            time_sensitive=False
        )
        
        # Route task
        if st.button("Route Task to Optimal Model"):
            demo_task = st.session_state.demo_data["task"]
            selection = st.session_state.router.route_task(demo_task, "workflow_001")
            
            st.success(f"Selected Model: {selection.routing_decision.selected_model.value}")
            st.markdown(f"**Confidence**: {selection.routing_decision.confidence:.2f}")
            st.markdown(f"**Quality Score**: {selection.routing_decision.quality_score:.2f}")
            st.markdown(f"**Estimated Time**: {selection.routing_decision.estimated_completion_time:.1f} min")
            
            st.markdown("### Routing Reasoning")
            st.markdown(selection.selection_reasoning)
            
            # Show alternatives
            if selection.routing_decision.alternatives:
                st.markdown("### Alternative Models")
                for alt_model, alt_score in selection.routing_decision.alternatives:
                    st.markdown(f"- {alt_model.value}: {alt_score:.2f}")
    
    with col2:
        st.subheader("📈 Performance Metrics")
        
        # Router statistics
        router_stats = st.session_state.router.get_routing_stats()
        st.json(router_stats)
        
        # Model capability comparison
        st.subheader("🥊 Model Comparison")
        
        comparison_data = []
        for model_cap in MODEL_CAPABILITIES:
            comparison_data.append({
                "Model": model_cap.display_name,
                "Reasoning": model_cap.capabilities.reasoning_long,
                "Code Backend": model_cap.capabilities.code_backend,
                "Code UI": model_cap.capabilities.code_ui,
                "Cost Score": model_cap.capabilities.cost_score,
                "Speed Score": model_cap.capabilities.latency_score
            })
        
        st.dataframe(comparison_data)
        
        # Load simulation
        st.subheader("⚡ Load Balancing")
        for model_type in [ModelType.CLAUDE_SONNET, ModelType.GPT4O, ModelType.GEMINI_FLASH]:
            load = st.session_state.router.current_loads.get(model_type, 0.0)
            st.metric(f"{model_type.value} Load", f"{load:.1%}")
        
        if st.button("Simulate Load"):
            import random
            for model_type in [ModelType.CLAUDE_SONNET, ModelType.GPT4O, ModelType.GEMINI_FLASH]:
                st.session_state.router.update_model_load(model_type, random.random())
            st.rerun()

def render_workflow_monitor():
    """Live workflow monitoring interface"""
    
    st.header("⚡ Live Workflow Monitor")
    
    orchestrator = st.session_state.orchestrator
    
    # Workflow overview
    col1, col2, col3, col4 = st.columns(4)
    
    status = orchestrator.get_workflow_status()
    
    with col1:
        st.metric("Total Events", status["total_events"])
    with col2:
        st.metric("Active Tasks", status["active_tasks"])
    with col3:
        st.metric("Completed Tasks", status["completed_tasks"]) 
    with col4:
        st.metric("Artifacts Produced", status["artifacts_produced"])
    
    # Event stream
    st.subheader("📜 Event Stream")
    
    if orchestrator.events:
        # Create event timeline
        for event in reversed(orchestrator.events[-10:]):  # Show last 10 events
            with st.container():
                col1, col2, col3 = st.columns([1, 2, 4])
                
                with col1:
                    st.caption(event.timestamp.strftime("%H:%M:%S"))
                
                with col2:
                    event_emoji = {
                        EventType.WORKFLOW_STARTED: "🚀 Started",
                        EventType.TASK_CREATED: "📋 Task Created", 
                        EventType.TASK_ASSIGNED: "👤 Assigned",
                        EventType.TASK_STARTED: "▶️ Started",
                        EventType.TASK_COMPLETED: "✅ Completed",
                        EventType.ARTIFACT_PRODUCED: "📄 Artifact",
                        EventType.AGENT_COMMUNICATION: "💬 Communication"
                    }.get(event.event_type, "📝 Event")
                    
                    st.markdown(f"**{event_emoji}**")
                
                with col3:
                    if event.task_id:
                        st.markdown(f"Task: {event.task_id}")
                    if event.agent_id:
                        st.markdown(f"Agent: {event.agent_id}")
                    
                    # Show event data summary
                    if event.data:
                        data_summary = f"Data: {list(event.data.keys())[:3]}"
                        st.caption(data_summary)
                
                st.markdown("---")
    else:
        st.info("No events in workflow. Start a workflow to see live monitoring.")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (5 seconds)")
    if auto_refresh:
        st.rerun()

def get_artifact_description(artifact_type: ArtifactType) -> str:
    """Get description for artifact type"""
    descriptions = {
        ArtifactType.SPEC_DOC: "Requirements and specifications document",
        ArtifactType.DESIGN_DOC: "Architecture and design decisions",
        ArtifactType.CODE_PATCH: "Code changes with unified diff format", 
        ArtifactType.TEST_PLAN: "Testing strategies and test cases",
        ArtifactType.EVAL_REPORT: "Quality assessment and metrics",
        ArtifactType.RUNBOOK: "Operational procedures and documentation"
    }
    return descriptions.get(artifact_type, "Unknown artifact type")

def create_artifact_template(artifact_type: ArtifactType) -> Dict[str, Any]:
    """Create template for artifact type"""
    
    base_template = {
        "artifact_id": f"template_{artifact_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "artifact_type": artifact_type.value,
        "created_by": "template_generator",
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "confidence": 0.8,
        "dependencies": [],
        "tags": ["template", "generated"]
    }
    
    if artifact_type == ArtifactType.SPEC_DOC:
        base_template.update({
            "title": "Template Specification",
            "objective": "Template objective",
            "requirements": [
                {"id": "REQ_001", "description": "Template requirement", "priority": "medium"}
            ],
            "acceptance_criteria": ["Template acceptance criteria"],
            "assumptions": ["Template assumptions"],
            "constraints": ["Template constraints"]
        })
    
    elif artifact_type == ArtifactType.CODE_PATCH:
        base_template.update({
            "title": "Template Code Patch", 
            "description": "Template code changes",
            "files_changed": [
                {"path": "example.py", "action": "modified", "lines_added": 10, "lines_removed": 5}
            ],
            "diff_unified": "--- a/example.py\n+++ b/example.py\n@@ -1,3 +1,4 @@\n # Example file\n+# Added comment\n def main():\n     pass",
            "language": "python",
            "test_instructions": ["Run template tests"]
        })
    
    return base_template

def check_api_connection() -> bool:
    """Check if FastAPI server is available"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def render_event_streaming_dashboard():
    """Real-time event streaming dashboard with Redis Streams"""
    
    st.header("🌊 Real-Time Event Streaming Dashboard")
    st.markdown("**Production-grade event-sourced orchestration with Redis Streams**")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📡 Event Stream Control")
        
        if st.session_state.api_connected:
            st.success("FastAPI Backend Connected")
            
            # Start workflow controls
            st.markdown("### Start New Workflow")
            workflow_name = st.text_input("Workflow Name", value="E-commerce API Development")
            
            if st.button("🚀 Start Real-Time Workflow"):
                try:
                    # Create task data
                    tasks = [
                        {
                            "task_id": "spec_generation",
                            "title": "Generate API Specification",
                            "goal": "Create comprehensive API spec",
                            "description": "Generate detailed API specification with endpoints and schemas"
                        },
                        {
                            "task_id": "design_architecture", 
                            "title": "Design System Architecture",
                            "goal": "Create system design",
                            "description": "Design scalable architecture with microservices"
                        }
                    ]
                    
                    # Start workflow via API
                    response = requests.post("http://localhost:8000/api/workflows/start", 
                                           json={"tasks": tasks, "workflow_name": workflow_name})
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Workflow started! Correlation ID: {data['correlation_id']}")
                        st.session_state.current_correlation_id = data['correlation_id']
                    else:
                        st.error(f"Failed to start workflow: {response.text}")
                
                except Exception as e:
                    st.error(f"Error starting workflow: {e}")
            
            # Artifact creation
            st.markdown("### Create Artifact")
            artifact_type = st.selectbox("Artifact Type", [at.value for at in ArtifactType])
            agent_id = st.selectbox("Creating Agent", ["claude_agent", "gpt4_agent", "gemini_agent"])
            
            if st.button("📄 Create Real-Time Artifact"):
                try:
                    correlation_id = st.session_state.get('current_correlation_id', 'demo_correlation')
                    
                    # Create artifact via API
                    artifact_content = {
                        "title": f"Real-time {artifact_type}",
                        "confidence": 0.9,
                        "content": f"Generated {artifact_type} with real-time event streaming"
                    }
                    
                    response = requests.post("http://localhost:8000/api/artifacts/create",
                                           json={
                                               "artifact_type": artifact_type,
                                               "content": artifact_content,
                                               "agent_id": agent_id,
                                               "correlation_id": correlation_id
                                           })
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Artifact created: {data['artifact_id']}")
                        st.json(data)
                    else:
                        st.error(f"Failed to create artifact: {response.text}")
                
                except Exception as e:
                    st.error(f"Error creating artifact: {e}")
        
        else:
            st.error("FastAPI Backend Not Available")
            st.markdown("""
            To enable real-time features:
            1. Start the FastAPI server: `python api_server.py`
            2. Optionally start Redis for full event streaming
            3. Refresh this page
            """)
    
    with col2:
        st.subheader("📊 Real-Time Statistics")
        
        if st.button("🔄 Refresh Stats"):
            if st.session_state.api_connected:
                try:
                    response = requests.get("http://localhost:8000/api/stats/real-time")
                    if response.status_code == 200:
                        stats = response.json()
                        st.json(stats)
                    else:
                        st.error("Failed to get stats")
                except Exception as e:
                    st.error(f"Stats error: {e}")
            else:
                # Show mock stats
                mock_stats = {
                    "workflow_id": "mock_workflow",
                    "mock_mode": True,
                    "message": "Start FastAPI server for real-time stats"
                }
                st.json(mock_stats)
        
        # Event stream display
        st.subheader("🌊 Live Event Stream")
        
        if st.session_state.get('current_correlation_id'):
            correlation_id = st.session_state.current_correlation_id
            
            if st.button("📜 Get Workflow Events"):
                try:
                    response = requests.get(f"http://localhost:8000/api/workflows/{correlation_id}/events")
                    if response.status_code == 200:
                        data = response.json()
                        st.markdown(f"**Events for {correlation_id}:**")
                        
                        for event in data.get('events', []):
                            with st.expander(f"{event['event_type']} - {event['timestamp'][:19]}"):
                                st.json(event)
                    else:
                        st.error("Failed to get events")
                except Exception as e:
                    st.error(f"Events error: {e}")
        else:
            st.info("Start a workflow to see live events")
    
    # Event replay section
    st.subheader("🔄 Event Replay & Time Travel")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Event Replay Controls")
        replay_correlation = st.text_input("Correlation ID for Replay", 
                                         value=st.session_state.get('current_correlation_id', ''))
        
        if st.button("🎬 Replay Events"):
            if replay_correlation and st.session_state.api_connected:
                try:
                    response = requests.get(f"http://localhost:8000/api/workflows/{replay_correlation}/events")
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Found {data['count']} events for replay")
                        
                        # Display events chronologically
                        st.markdown("### Event Timeline")
                        for i, event in enumerate(data.get('events', [])):
                            st.markdown(f"**{i+1}.** {event['event_type']} at {event['timestamp'][:19]}")
                            if event.get('agent_id'):
                                st.markdown(f"   👤 Agent: {event['agent_id']}")
                            if event.get('payload'):
                                with st.expander("View Event Data"):
                                    st.json(event['payload'])
                except Exception as e:
                    st.error(f"Replay error: {e}")
    
    with col2:
        st.markdown("### Real-Time Collaboration Feed")
        
        if st.session_state.real_time_orchestrator:
            st.info("Event streaming system ready")
            
            # Simulate some real-time events for demo
            if st.button("🎭 Simulate Agent Activity"):
                # Add mock events to session state
                mock_events = [
                    {"type": "agent_started", "agent": "claude_agent", "task": "spec_generation"},
                    {"type": "artifact_created", "agent": "claude_agent", "artifact": "spec_doc_001"},
                    {"type": "review_requested", "artifact": "spec_doc_001", "reviewer": "gpt4_agent"},
                    {"type": "agent_started", "agent": "gpt4_agent", "task": "design_architecture"}
                ]
                
                st.session_state.event_stream.extend(mock_events)
                
                for event in mock_events:
                    st.markdown(f"🔄 **{event['type']}** - {event.get('agent', 'system')}")
        else:
            st.warning("Event streaming not initialized")

def render_live_ai_project_launcher():
    """Live AI project launcher with real agent coordination"""
    
    st.header("🤖 Live AI Agent Collaboration")
    st.markdown("**Start a real project where Claude, GPT-4, and Gemini agents collaborate**")
    
    # Check API key availability
    api_keys = {
        'Claude': bool(os.environ.get('ANTHROPIC_API_KEY')),
        'GPT-4': bool(os.environ.get('OPENAI_API_KEY')),
        'Gemini': bool(os.environ.get('GEMINI_API_KEY'))
    }
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "🟢 Ready" if api_keys['Claude'] else "🔴 Missing Key"
        st.markdown(f"**Claude**: {status}")
        
    with col2:
        status = "🟢 Ready" if api_keys['GPT-4'] else "🔴 Missing Key"
        st.markdown(f"**GPT-4**: {status}")
        
    with col3:
        status = "🟢 Ready" if api_keys['Gemini'] else "🔴 Missing Key"
        st.markdown(f"**Gemini**: {status}")
    
    available_agents = sum(api_keys.values())
    
    if available_agents == 0:
        st.error("No AI agents available. Please configure API keys.")
        return
    elif available_agents < 3:
        st.warning(f"Only {available_agents}/3 agents available. Project will use available agents.")
    else:
        st.success("All AI agents ready for collaboration!")
    
    # Project configuration
    st.subheader("🎯 Project Configuration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        project_description = st.text_area(
            "Project Description",
            value="Build a RESTful API for a task management system with user authentication, task CRUD operations, and real-time notifications.",
            height=100,
            help="Describe what you want the AI agents to build together"
        )
        
    with col2:
        project_type = st.selectbox(
            "Project Type",
            options=["web_application", "api", "ui_application", "data_pipeline", "mobile_app"],
            help="Type of project affects the workflow phases"
        )
        
        complexity_level = st.selectbox(
            "Complexity Level",
            options=["Simple", "Medium", "Complex", "Advanced"],
            index=1
        )
    
    # Workflow preview
    st.subheader("🔄 Planned Workflow")
    
    workflow_preview = {
        "web_application": [
            "📋 Requirements Analysis (Claude)",
            "🏗️ System Architecture (Claude)", 
            "💻 Core Implementation (GPT-4)",
            "🎨 UI Development (GPT-4)",
            "🧪 Testing & QA (Gemini)",
            "📚 Documentation (Claude)"
        ],
        "api": [
            "📋 API Specification (Claude)",
            "🏗️ System Architecture (Claude)",
            "💻 Core Implementation (GPT-4)", 
            "🧪 Testing & QA (Gemini)",
            "📚 API Documentation (Claude)"
        ],
        "ui_application": [
            "📋 UI Requirements (Claude)",
            "🎨 Design System (GPT-4)",
            "💻 Component Implementation (GPT-4)",
            "🧪 UI Testing (Gemini)",
            "📚 User Documentation (Claude)"
        ]
    }
    
    phases = workflow_preview.get(project_type, workflow_preview["web_application"])
    
    for i, phase in enumerate(phases, 1):
        st.markdown(f"**{i}.** {phase}")
    
    # Quality cascade explanation
    with st.expander("🔄 Quality Cascade Process"):
        st.markdown("""
        **Multi-Agent Quality Assurance:**
        - Each phase includes automated quality reviews
        - Agents review each other's work for optimal results
        - Architecture: Claude → GPT-4 → Gemini validation
        - Implementation: GPT-4 → Claude review → Gemini testing  
        - Testing: Gemini → GPT-4 review → Claude analysis
        
        **Real-time Collaboration:**
        - Live agent activity monitoring
        - Automatic handoffs between phases
        - Conflict resolution when agents disagree
        - Cost and performance tracking
        """)
    
    # Launch controls
    st.subheader("🚀 Launch Project")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("▶️ Start Live AI Project", type="primary", disabled=available_agents == 0):
            if project_description.strip():
                # Initialize live orchestrator
                try:
                    if 'live_orchestrator' not in st.session_state:
                        from core.live_orchestrator import LiveOrchestrator
                        st.session_state.live_orchestrator = LiveOrchestrator()
                    
                    # Start project
                    with st.spinner("Initializing live AI agents..."):
                        correlation_id = asyncio.run(
                            st.session_state.live_orchestrator.start_live_project(
                                project_description, project_type.lower()
                            )
                        )
                    
                    st.session_state.active_live_project = correlation_id
                    st.success(f"Live project started! Correlation ID: {correlation_id}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to start live project: {e}")
                    st.exception(e)
            else:
                st.error("Please provide a project description")
    
    with col2:
        if st.button("📊 View Active Projects"):
            st.rerun()
    
    # Show active projects
    if hasattr(st.session_state, 'live_orchestrator') and st.session_state.live_orchestrator:
        active_projects = st.session_state.live_orchestrator.get_all_live_projects()
        
        if active_projects:
            st.subheader("📈 Active Live Projects")
            
            for project in active_projects:
                with st.expander(f"Project: {project['correlation_id']} ({project['status']})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Description**: {project['description']}")
                        st.markdown(f"**Current Phase**: {project['current_phase_name']}")
                        st.progress(project['progress_percentage'] / 100)
                        st.caption(f"Progress: {project['progress_percentage']:.1f}%")
                        
                    with col2:
                        st.metric("Artifacts", project['artifacts_created'])
                        st.metric("Phases", f"{project['current_phase']}/{project['total_phases']}")
                        
                        if project['agent_assignments']:
                            st.markdown("**Agent Assignments:**")
                            for phase, agent in project['agent_assignments'].items():
                                st.caption(f"• {phase}: {agent}")
        
        # Orchestrator metrics
        if st.button("📊 View Orchestrator Metrics"):
            try:
                metrics = st.session_state.live_orchestrator.get_orchestrator_metrics()
                st.json(metrics)
            except Exception as e:
                st.error(f"Failed to get metrics: {e}")

if __name__ == "__main__":
    main()