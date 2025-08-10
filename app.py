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
import openai

# Schema imports
from schemas.artifacts import ArtifactType, SpecDoc, DesignDoc, CodePatch, TestPlan, EvalReport, Runbook
from schemas.ledgers import TaskLedger, ProgressLedger, WorkItem, TaskStatus, Priority
from schemas.routing import ModelType, TaskType, TaskComplexity, ModelRouter, MODEL_CAPABILITIES

# Core system imports  
from core.orchestrator import EventSourcedOrchestrator, EventType, WorkflowEvent
from core.router import DataDrivenRouter, RoutingContext
from core.artifacts import ArtifactValidator, ArtifactHandler
from core.event_streaming import RealTimeEventOrchestrator, EventBus, StreamEvent, EventType as StreamEventType, EventStreamType

# Enhanced intelligent routing imports
from core.model_router import IntelligentRouter
from schemas.outcomes import TaskOutcome
from core.cost_governor import CostGovernor, ProjectComplexity
from monitoring.performance_tracker import PerformanceTracker

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
    
    if 'intelligent_router' not in st.session_state:
        try:
            st.session_state.intelligent_router = IntelligentRouter()
        except Exception as e:
            st.session_state.intelligent_router = None
            logger.warning(f"Could not initialize intelligent router: {e}")
    
    if 'artifact_handler' not in st.session_state:
        st.session_state.artifact_handler = ArtifactHandler()
    
    # Initialize typed artifact system
    if 'typed_artifact_handler' not in st.session_state:
        from core.artifact_handler import TypedArtifactHandler
        st.session_state.typed_artifact_handler = TypedArtifactHandler()
    
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
    
    # Project configuration session state
    if 'project_configured' not in st.session_state:
        st.session_state.project_configured = False
    
    if 'project_description' not in st.session_state:
        st.session_state.project_description = "Build a RESTful API for a task management system with user authentication, task CRUD operations, and real-time notifications."
    
    if 'project_type' not in st.session_state:
        st.session_state.project_type = "api"
    
    if 'complexity_level' not in st.session_state:
        st.session_state.complexity_level = "Medium"
    
    if 'configuration_step' not in st.session_state:
        st.session_state.configuration_step = 1  # 1: Configure, 2: Review, 3: Launch, 4: Monitor
    
    if 'active_live_project' not in st.session_state:
        st.session_state.active_live_project = None

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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🤖 Intelligent Router",
        "🎯 Typed Artifact System",
        "📋 Schema Demonstration",
        "🎯 Task & Artifact Management", 
        "🤖 Agent Orchestration",
        "📊 Routing & Performance",
        "⚡ Live Workflow Monitor",
        "🌊 Event Streaming (New)"
    ])
    
    with tab1:
        render_intelligent_router()
    
    with tab2:
        render_typed_artifacts_page()
    
    with tab3:
        render_schema_demo()
    
    with tab4:
        render_task_management()
    
    with tab5:
        render_agent_orchestration()
        
    with tab6:
        render_routing_dashboard()
    
    with tab7:
        render_workflow_monitor()
    
    with tab8:
        render_event_streaming_dashboard()

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
    """Agent orchestration and live project management"""
    
    st.header("🤖 Live AI Agent Collaboration")
    
    # Progress indicator
    step_names = ["Configure", "Review", "Launch", "Monitor"]
    current_step = st.session_state.configuration_step
    
    progress_cols = st.columns(4)
    for i, step_name in enumerate(step_names, 1):
        with progress_cols[i-1]:
            if i < current_step:
                st.markdown(f"✅ **{step_name}**")
            elif i == current_step:
                st.markdown(f"🔄 **{step_name}**")
            else:
                st.markdown(f"⚪ {step_name}")
    
    st.markdown("---")
    
    # Step 1: Project Configuration
    if current_step == 1:
        render_project_configuration()
    
    # Step 2: Review and Planning
    elif current_step == 2:
        render_project_review()
    
    # Step 3: Launch Controls
    elif current_step == 3:
        render_project_launch()
    
    # Step 4: Live Monitoring
    elif current_step == 4:
        render_live_monitoring()

def render_project_configuration():
    """Step 1: Project Configuration"""
    
    st.subheader("🎯 Step 1: Configure Your Project")
    
    # Check API key availability
    api_keys = {
        'Claude': bool(os.environ.get('ANTHROPIC_API_KEY')),
        'GPT-4': bool(os.environ.get('OPENAI_API_KEY')),
        'Gemini': bool(os.environ.get('GEMINI_API_KEY'))
    }
    
    # API Status
    st.markdown("#### AI Agent Status")
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
        st.error("⚠️ No AI agents available. Please configure API keys to proceed.")
        return
    elif available_agents < 3:
        st.warning(f"⚠️ Only {available_agents}/3 agents available. Project will use available agents.")
    else:
        st.success("✅ All AI agents ready for collaboration!")
    
    st.markdown("---")
    
    # Project configuration form
    st.markdown("#### Project Details")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        project_description = st.text_area(
            "Project Description",
            value=st.session_state.project_description,
            height=120,
            help="Describe what you want the AI agents to build together",
            key="project_desc_input"
        )
        
        # Update session state when changed
        if project_description != st.session_state.project_description:
            st.session_state.project_description = project_description
        
    with col2:
        project_type = st.selectbox(
            "Project Type",
            options=["web_application", "api", "ui_application", "data_pipeline", "mobile_app"],
            index=["web_application", "api", "ui_application", "data_pipeline", "mobile_app"].index(st.session_state.project_type),
            help="Type of project affects the workflow phases",
            key="project_type_input"
        )
        
        # Update session state when changed
        if project_type != st.session_state.project_type:
            st.session_state.project_type = project_type
        
        complexity_level = st.selectbox(
            "Complexity Level",
            options=["Simple", "Medium", "Complex", "Advanced"],
            index=["Simple", "Medium", "Complex", "Advanced"].index(st.session_state.complexity_level),
            key="complexity_input"
        )
        
        # Update session state when changed
        if complexity_level != st.session_state.complexity_level:
            st.session_state.complexity_level = complexity_level
    
    # Configuration validation
    current_description = st.session_state.project_description or ""
    config_valid = (
        current_description.strip() != "" and
        len(current_description.strip()) >= 20 and
        available_agents > 0
    )
    
    if not config_valid:
        if not current_description.strip():
            st.error("Please provide a project description")
        elif len(current_description.strip()) < 20:
            st.error("Project description should be at least 20 characters")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("📋 Review Configuration", type="primary", disabled=not config_valid):
            st.session_state.configuration_step = 2
            st.session_state.project_configured = True
            st.rerun()
    
    with col3:
        if st.button("🔄 Reset Configuration"):
            # Reset to defaults
            st.session_state.project_description = "Build a RESTful API for a task management system with user authentication, task CRUD operations, and real-time notifications."
            st.session_state.project_type = "api"
            st.session_state.complexity_level = "Medium"
            st.session_state.configuration_step = 1
            st.session_state.project_configured = False
            st.rerun()

def render_project_review():
    """Step 2: Review and Planning"""
    
    st.subheader("📋 Step 2: Review Your Project Plan")
    
    # Configuration Summary
    with st.container():
        st.markdown("#### Project Configuration Summary")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Description:** {st.session_state.project_description}")
            
        with col2:
            st.markdown(f"**Type:** {st.session_state.project_type.replace('_', ' ').title()}")
            st.markdown(f"**Complexity:** {st.session_state.complexity_level}")
    
    # Workflow preview
    st.markdown("#### 🔄 Planned Agent Workflow")
    
    workflow_preview = {
        "web_application": [
            ("📋 Requirements Analysis", "Claude", "Analyze requirements and create project specification"),
            ("🏗️ System Architecture", "Claude", "Design system architecture and component structure"), 
            ("💻 Core Implementation", "GPT-4", "Implement core business logic and backend services"),
            ("🎨 UI Development", "GPT-4", "Create user interface and frontend components"),
            ("🧪 Testing & QA", "Gemini", "Generate comprehensive tests and quality assurance"),
            ("📚 Documentation", "Claude", "Create complete project documentation")
        ],
        "api": [
            ("📋 API Specification", "Claude", "Define API endpoints and data contracts"),
            ("🏗️ System Architecture", "Claude", "Design scalable API architecture"),
            ("💻 Core Implementation", "GPT-4", "Implement API endpoints and business logic"), 
            ("🧪 Testing & QA", "Gemini", "Create API tests and validation"),
            ("📚 API Documentation", "Claude", "Generate comprehensive API documentation")
        ],
        "ui_application": [
            ("📋 UI Requirements", "Claude", "Analyze UI requirements and user flows"),
            ("🎨 Design System", "GPT-4", "Create design system and component library"),
            ("💻 Component Implementation", "GPT-4", "Build interactive UI components"),
            ("🧪 UI Testing", "Gemini", "Test user interface and interactions"),
            ("📚 User Documentation", "Claude", "Create user guides and documentation")
        ],
        "data_pipeline": [
            ("📋 Data Requirements", "Claude", "Analyze data sources and requirements"),
            ("🏗️ Pipeline Architecture", "Claude", "Design data processing architecture"),
            ("💻 Pipeline Implementation", "GPT-4", "Build data processing pipeline"),
            ("🧪 Data Validation", "Gemini", "Test data quality and pipeline reliability"),
            ("📚 Pipeline Documentation", "Claude", "Document pipeline operations and maintenance")
        ],
        "mobile_app": [
            ("📋 App Requirements", "Claude", "Define mobile app requirements and features"),
            ("🎨 UI/UX Design", "GPT-4", "Design mobile user interface and experience"),
            ("💻 App Implementation", "GPT-4", "Develop mobile application"),
            ("🧪 App Testing", "Gemini", "Test app functionality and user experience"),
            ("📚 App Documentation", "Claude", "Create app documentation and guides")
        ]
    }
    
    phases = workflow_preview.get(st.session_state.project_type, workflow_preview["web_application"])
    
    for i, (phase_name, agent, description) in enumerate(phases, 1):
        with st.container():
            col1, col2, col3 = st.columns([0.5, 2, 1])
            
            with col1:
                st.markdown(f"**{i}.**")
            
            with col2:
                st.markdown(f"**{phase_name}**")
                st.caption(description)
            
            with col3:
                agent_color = {"Claude": "🟦", "GPT-4": "🟩", "Gemini": "🟨"}
                st.markdown(f"{agent_color.get(agent, '🟪')} **{agent}**")
    
    # Cost and time estimation
    st.markdown("#### 💰 Estimated Project Metrics")
    
    complexity_multipliers = {
        "Simple": 1.0,
        "Medium": 1.5,
        "Complex": 2.2,
        "Advanced": 3.0
    }
    
    base_phases = len(phases)
    multiplier = complexity_multipliers[st.session_state.complexity_level]
    estimated_time = int(base_phases * 8 * multiplier)  # minutes
    estimated_cost = round(base_phases * 0.50 * multiplier, 2)  # USD
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Estimated Time", f"{estimated_time} minutes")
    
    with col2:
        st.metric("Estimated Cost", f"${estimated_cost}")
    
    with col3:
        st.metric("Total Phases", f"{base_phases}")
    
    # Quality cascade explanation
    with st.expander("🔄 Quality Assurance Process"):
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
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Back to Configuration"):
            st.session_state.configuration_step = 1
            st.rerun()
    
    with col2:
        if st.button("🚀 Launch Project", type="primary"):
            st.session_state.configuration_step = 3
            st.rerun()

def render_project_launch():
    """Step 3: Launch Controls"""
    
    st.subheader("🚀 Step 3: Launch Your AI Project")
    
    st.markdown("#### Final Confirmation")
    st.info("You're about to start a live AI collaboration project. The agents will work together to build your project using real API calls.")
    
    # Project summary
    with st.container():
        st.markdown("**Project Summary:**")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"• **Description:** {st.session_state.project_description[:100]}...")
            st.markdown(f"• **Type:** {st.session_state.project_type.replace('_', ' ').title()}")
            st.markdown(f"• **Complexity:** {st.session_state.complexity_level}")
        
        with col2:
            # Check API availability one more time
            api_keys = {
                'Claude': bool(os.environ.get('ANTHROPIC_API_KEY')),
                'GPT-4': bool(os.environ.get('OPENAI_API_KEY')),
                'Gemini': bool(os.environ.get('GEMINI_API_KEY'))
            }
            available_agents = sum(api_keys.values())
            st.markdown(f"**Available Agents:** {available_agents}/3")
    
    # Launch controls
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Review Plan"):
            st.session_state.configuration_step = 2
            st.rerun()
    
    with col2:
        launch_disabled = available_agents == 0 or not st.session_state.project_description.strip()
        
        if st.button("▶️ Start Live AI Project", type="primary", disabled=launch_disabled):
            if st.session_state.project_description.strip():
                # Initialize live orchestrator
                try:
                    if 'live_orchestrator' not in st.session_state:
                        from core.live_orchestrator import LiveOrchestrator
                        st.session_state.live_orchestrator = LiveOrchestrator()
                    
                    # Start project
                    with st.spinner("🤖 Initializing live AI agents..."):
                        correlation_id = asyncio.run(
                            st.session_state.live_orchestrator.start_live_project(
                                st.session_state.project_description, 
                                st.session_state.project_type.lower()
                            )
                        )
                    
                    st.session_state.active_live_project = correlation_id
                    st.session_state.configuration_step = 4
                    st.success(f"🎉 Live project started! Correlation ID: {correlation_id}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to start live project: {e}")
                    if "import" in str(e).lower():
                        st.warning("Live orchestrator not available. Showing demo mode instead.")
                        st.session_state.configuration_step = 4
                        st.session_state.active_live_project = "demo_mode"
                        st.rerun()
            else:
                st.error("Please provide a project description")
    
    with col3:
        if st.button("🔄 Start Over"):
            # Reset everything
            st.session_state.configuration_step = 1
            st.session_state.project_configured = False
            st.session_state.active_live_project = None
            st.rerun()

def render_live_monitoring():
    """Step 4: Live Project Monitoring"""
    
    st.subheader("📊 Step 4: Live Project Monitoring")
    
    if st.session_state.active_live_project:
        correlation_id = st.session_state.active_live_project
        
        # Project header
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**Project ID:** `{correlation_id}`")
            st.markdown(f"**Status:** {'🟢 Active' if correlation_id != 'demo_mode' else '🟡 Demo Mode'}")
        
        with col2:
            if st.button("🔄 Refresh Status"):
                st.rerun()
        
        with col3:
            if st.button("⏹️ Stop Project"):
                st.session_state.active_live_project = None
                st.session_state.configuration_step = 1
                st.success("Project stopped successfully")
                st.rerun()
        
        st.markdown("---")
        
        # Show active projects or demo
        if correlation_id == "demo_mode":
            render_demo_monitoring()
        else:
            render_real_monitoring(correlation_id)
        
        # Quick actions
        st.markdown("#### Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 View All Projects"):
                st.rerun()
        
        with col2:
            if st.button("🆕 Start New Project"):
                st.session_state.configuration_step = 1
                st.session_state.project_configured = False
                st.session_state.active_live_project = None
                st.rerun()
        
        with col3:
            if st.button("📈 View Metrics"):
                if hasattr(st.session_state, 'live_orchestrator') and st.session_state.live_orchestrator:
                    try:
                        metrics = st.session_state.live_orchestrator.get_orchestrator_metrics()
                        st.json(metrics)
                    except Exception as e:
                        st.error(f"Failed to get metrics: {e}")
    else:
        st.warning("No active project. Please start a new project.")
        if st.button("🆕 Start New Project"):
            st.session_state.configuration_step = 1
            st.rerun()

def render_demo_monitoring():
    """Demo monitoring interface"""
    st.info("🎭 Demo Mode - Simulated AI agent collaboration")
    
    # Simulate progress
    import random
    progress = min(random.randint(25, 85), 85)
    
    st.progress(progress / 100)
    st.caption(f"Progress: {progress}%")
    
    # Simulated agent activity
    st.markdown("#### 🤖 Agent Activity")
    
    demo_activities = [
        {"agent": "Claude", "task": "Requirements Analysis", "status": "✅ Complete"},
        {"agent": "Claude", "task": "System Architecture", "status": "🔄 In Progress"},
        {"agent": "GPT-4", "task": "Core Implementation", "status": "⏳ Queued"},
        {"agent": "Gemini", "task": "Testing & QA", "status": "⏳ Queued"},
    ]
    
    for activity in demo_activities:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.markdown(f"**{activity['agent']}**")
        
        with col2:
            st.markdown(activity['task'])
        
        with col3:
            st.markdown(activity['status'])

def render_real_monitoring(correlation_id):
    """Real project monitoring interface with actual AI agent results"""
    
    if hasattr(st.session_state, 'live_orchestrator') and st.session_state.live_orchestrator:
        try:
            # Get real agent results
            real_results = st.session_state.live_orchestrator.get_real_agent_results(correlation_id)
            project_progress = st.session_state.live_orchestrator.get_project_progress(correlation_id)
            
            if project_progress:
                # Project overview
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**Description**: {project_progress['description']}")
                    status_emoji = "🟢" if project_progress['status'] == 'completed' else "🔄" if project_progress['status'] == 'active' else "🔴"
                    st.markdown(f"**Status**: {status_emoji} {project_progress['status'].title()}")
                    
                with col2:
                    st.metric("Progress", f"{project_progress['progress_percentage']:.0f}%")
                    st.progress(project_progress['progress_percentage'] / 100)
                    
                with col3:
                    st.metric("Phases Complete", f"{project_progress['phases_completed']}/{project_progress['total_phases']}")
                    st.metric("AI Agents", len(real_results))
                
                st.markdown("---")
                
                # Real Agent Results
                if real_results:
                    st.markdown("#### 🤖 Real AI Agent Collaboration Results")
                    
                    for i, result in enumerate(real_results):
                        with st.expander(f"🎯 {result['agent']} - {result['phase']}", expanded=(i < 2)):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                # Display agent result
                                if isinstance(result['result'], dict):
                                    if 'analysis' in result['result']:
                                        st.markdown("**Analysis:**")
                                        st.write(result['result']['analysis'])
                                    
                                    if 'tasks' in result['result']:
                                        st.markdown("**Task Breakdown:**")
                                        for task in result['result'].get('tasks', [])[:3]:  # Show first 3 tasks
                                            if isinstance(task, dict):
                                                st.markdown(f"• **{task.get('title', 'Task')}**: {task.get('description', 'No description')}")
                                    
                                    if 'approach' in result['result']:
                                        st.markdown("**Technical Approach:**")
                                        st.write(result['result']['approach'])
                                    
                                    if 'design_approach' in result['result']:
                                        st.markdown("**Design Approach:**")
                                        st.write(result['result']['design_approach'])
                                    
                                    if 'strategy' in result['result']:
                                        st.markdown("**Testing Strategy:**")
                                        st.write(result['result']['strategy'])
                                    
                                    # Show full result in JSON format
                                    with st.expander("📋 Full Agent Output"):
                                        st.json(result['result'])
                                else:
                                    st.write(str(result['result']))
                            
                            with col2:
                                status_color = "🟢" if result['status'] == 'completed' else "🔴"
                                st.markdown(f"**Status**: {status_color} {result['status']}")
                                st.markdown(f"**Time**: {result['timestamp'][:19]}")
                
                else:
                    st.info("🔄 AI agents are working on your project. Real results will appear here as they complete their tasks.")
                    
                    # Show loading animation
                    with st.spinner("Real AI agents are collaborating on your project..."):
                        import time
                        time.sleep(1)  # Brief pause for effect
                
                # Project completion summary
                if project_progress['status'] == 'completed':
                    st.success("🎉 Project completed successfully!")
                    st.markdown("#### 📊 Project Summary")
                    
                    summary_col1, summary_col2 = st.columns(2)
                    with summary_col1:
                        if project_progress.get('start_time'):
                            st.markdown(f"**Started**: {project_progress['start_time']}")
                        if project_progress.get('completion_time'):
                            st.markdown(f"**Completed**: {project_progress['completion_time']}")
                    
                    with summary_col2:
                        st.markdown(f"**Total Artifacts**: {project_progress['artifacts_created']}")
                        st.markdown(f"**AI Models Used**: Claude, GPT-4, Gemini")
            
            else:
                st.warning(f"Project {correlation_id} not found")
                
        except Exception as e:
            st.error(f"Failed to get real agent results: {e}")
            st.markdown("**Error Details:**")
            st.code(str(e))
            render_demo_monitoring()
    else:
        st.warning("Live orchestrator not available. Showing demo mode.")
        render_demo_monitoring()

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
    """Check if OpenAI API key is available"""
    try:
        # Check if OpenAI API key is available
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return False
        
        # Basic validation - should start with 'sk-' and be reasonable length
        if api_key.startswith('sk-') and len(api_key) > 20:
            return True
        
        return False
    except Exception as e:
        logger.error(f"API connection check failed: {e}")
        return False

def render_typed_artifacts_page():
    """Render the Typed Artifact System demonstration page"""
    st.header("🎯 Typed Artifact System")
    st.markdown("""
    **Enhanced multi-agent collaboration with strict schema enforcement**
    
    This system provides structured handoffs, conflict resolution, and quality tracking 
    for AI agent collaboration through typed artifacts.
    """)
    
    # Import the integration module
    try:
        from integration_typed_artifacts import TypedArtifactOrchestrator
        
        # Initialize orchestrator
        if 'typed_orchestrator' not in st.session_state:
            st.session_state.typed_orchestrator = TypedArtifactOrchestrator()
        
        orchestrator = st.session_state.typed_orchestrator
        
        # Get current metrics
        metrics = orchestrator.get_system_metrics()
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Artifacts", metrics['artifacts']['total_artifacts'])
        
        with col2:
            st.metric("Avg Quality", f"{metrics['artifacts']['avg_quality']:.2f}")
        
        with col3:
            st.metric("Handoff Success", f"{metrics['handoffs'].get('success_rate', 1.0):.1%}")
        
        with col4:
            st.metric("System Health", f"{metrics['system_health']['score']:.2f}")
        
        # System health indicator
        health = metrics['system_health']
        health_color = {
            'excellent': '🟢',
            'good': '🟡', 
            'fair': '🟠',
            'poor': '🔴'
        }.get(health['level'], '⚪')
        
        st.markdown(f"**System Health:** {health_color} {health['level'].title()} ({health['score']:.2f})")
        
        if health['issues']:
            st.warning("**Issues Detected:**\n" + "\n".join(f"• {issue}" for issue in health['issues']))
        
        if health['recommendations']:
            st.info("**Recommendations:**\n" + "\n".join(f"• {rec}" for rec in health['recommendations']))
        
        # Demo section
        st.subheader("🚀 Live Demonstration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Create Sample SpecDoc", type="primary"):
                # Create a sample SpecDoc
                spec_data = {
                    "title": "Sample E-commerce Platform",
                    "objective": "Build a modern e-commerce platform with user authentication and product catalog",
                    "scope": "Full-stack web application",
                    "requirements": [
                        {
                            "id": "REQ-001",
                            "description": "User authentication system with secure login",
                            "priority": "high"
                        }
                    ],
                    "acceptance_criteria": ["Users can register and login securely"],
                    "business_value": "Increase online sales by 30%"
                }
                
                result = orchestrator.create_artifact_from_agent_output(
                    agent_id="project_manager",
                    agent_output=str(spec_data),
                    artifact_type="SpecDoc",
                    context={"demo": True}
                )
                
                if result['success']:
                    st.success(f"Created SpecDoc: {result['artifact_id']}")
                    st.json({
                        "artifact_id": result['artifact_id'],
                        "confidence": result['confidence'],
                        "quality_score": result['quality_score']
                    })
                else:
                    st.error(f"Failed to create artifact: {result['details']}")
        
        with col2:
            if st.button("Run Conflict Detection"):
                artifact_ids = list(st.session_state.typed_artifacts.get('artifacts', {}).keys())
                
                if len(artifact_ids) >= 2:
                    result = orchestrator.detect_and_resolve_conflicts(artifact_ids[-2:])
                    
                    st.info(f"Checked {len(artifact_ids)} artifacts for conflicts")
                    if result['conflicts_found'] > 0:
                        st.warning(f"Found {result['conflicts_found']} conflicts")
                        for conflict in result['conflicts']:
                            st.write(f"• {conflict['conflict_type']}: {conflict['description']}")
                    else:
                        st.success("No conflicts detected")
                else:
                    st.info("Need at least 2 artifacts to detect conflicts")
        
        # Artifacts breakdown
        if metrics['artifacts']['total_artifacts'] > 0:
            st.subheader("📊 Artifact Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**By Type:**")
                for artifact_type, count in metrics['artifacts']['by_type'].items():
                    st.write(f"• {artifact_type}: {count}")
            
            with col2:
                st.write("**By Agent:**")
                for agent, count in metrics['artifacts']['by_agent'].items():
                    st.write(f"• {agent}: {count}")
        
        # Recent activity
        st.subheader("🔄 Recent Activity")
        
        if 'typed_artifacts' in st.session_state:
            recent_artifacts = list(st.session_state.typed_artifacts['artifacts'].values())[-5:]
            if recent_artifacts:
                for artifact_data in recent_artifacts:
                    artifact = artifact_data['artifact']
                    with st.expander(f"{artifact['artifact_type']}: {artifact.get('title', 'Untitled')}"):
                        st.write(f"**ID:** {artifact['artifact_id']}")
                        st.write(f"**Created by:** {artifact['created_by']}")
                        st.write(f"**Confidence:** {artifact_data['confidence_metrics']['overall_confidence']:.2f}")
                        st.write(f"**Quality:** {artifact_data['validation_result']['quality_score']:.2f}")
            else:
                st.info("No artifacts created yet")
        else:
            st.info("No artifacts created yet")
        
    except ImportError as e:
        st.error(f"Could not load Typed Artifact System: {e}")
        st.info("The typed artifact system components may not be properly installed.")
    except Exception as e:
        st.error(f"Error in Typed Artifact System: {e}")
        st.code(str(e))


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


def render_intelligent_router():
    """Render the Intelligent Router with Learning interface"""
    st.header("🤖 Intelligent Model Router with Learning")
    st.markdown("Advanced router using Thompson Sampling bandit learning and cost governance")
    
    if not st.session_state.intelligent_router:
        st.warning("Intelligent Router not available. Please check system configuration.")
        return
    
    router = st.session_state.intelligent_router
    
    # Router Status and Controls
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.subheader("🎯 Router Status")
        st.metric("Models Available", len(router.capability_vectors))
        st.metric("Total Routing Requests", router.bandit.total_interactions)
        
    with col2:
        st.subheader("💰 Cost Management")
        try:
            usage_summary = router.cost_governor.get_usage_summary("demo_project")
            if 'current_usage' in usage_summary:
                usage = usage_summary['current_usage']
                budget = usage_summary['budget_limits']
                utilization = usage_summary['utilization']
                
                st.metric("Token Usage", f"{usage['tokens_used']:,} / {budget['max_tokens']:,}")
                st.metric("Cost Utilization", f"{utilization['cost_percent']:.1f}%")
                st.metric("Requests Made", usage['requests_made'])
            else:
                st.info("No usage data available yet")
        except Exception as e:
            st.error(f"Error loading cost data: {e}")
    
    with col3:
        st.subheader("📊 Performance Metrics")
        try:
            bandit_stats = router.bandit.get_arm_statistics()
            if bandit_stats:
                best_performing = max(bandit_stats.items(), key=lambda x: x[1]['estimated_mean'])
                st.metric("Best Model", best_performing[0])
                st.metric("Best Performance", f"{best_performing[1]['estimated_mean']:.3f}")
                st.metric("Confidence", f"±{(best_performing[1]['confidence_interval'][1] - best_performing[1]['confidence_interval'][0])/2:.3f}")
            else:
                st.info("No performance data available yet")
        except Exception as e:
            st.error(f"Error loading performance data: {e}")
    
    # Interactive Router Demo
    st.subheader("🎮 Interactive Router Demo")
    
    with st.expander("Create Demo Task", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            task_description = st.text_area(
                "Task Description",
                value="Design a comprehensive microservices architecture for an e-commerce platform",
                height=100
            )
        
        with col2:
            task_type = st.selectbox("Task Type", options=[t.value for t in TaskType])
            complexity_level = st.slider("Complexity Level", 0.0, 1.0, 0.7, 0.1)
            project_complexity = st.selectbox("Project Complexity", 
                                            options=[c.value for c in ProjectComplexity])
            time_sensitive = st.checkbox("Time Sensitive")
        
        if st.button("🚀 Route Task", type="primary"):
            try:
                # Create task
                task = {
                    'description': task_description,
                    'context': {
                        'task_type': TaskType(task_type),
                        'project_complexity': project_complexity,
                        'estimated_tokens': int(1000 + complexity_level * 3000),
                        'time_sensitive': time_sensitive,
                        'cost_sensitive': False,
                        'quality_priority': 0.8,
                        'complexity_level': complexity_level
                    }
                }
                
                # Route the task
                routing_decision = router.route_task(task, task['context'])
                
                # Display results
                st.success(f"✅ Task routed to: **{routing_decision['selected_model'].value}**")
                st.metric("Routing Score", f"{routing_decision['routing_score']:.3f}")
                
                # Show decision breakdown
                decision_factors = routing_decision.get('decision_factors', {})
                if decision_factors:
                    st.subheader("📋 Decision Breakdown")
                    factors_df = {
                        'Factor': ['Capability', 'Bandit Score', 'Quality', 'Cost', 'Latency', 'Exploration'],
                        'Score': [
                            decision_factors.get('capability_score', 0),
                            decision_factors.get('bandit_score', 0),
                            decision_factors.get('quality_component', 0),
                            decision_factors.get('cost_component', 0),
                            decision_factors.get('latency_component', 0),
                            decision_factors.get('exploration_bonus', 0)
                        ]
                    }
                    st.bar_chart(factors_df)
                
                # Show alternatives
                alternatives = routing_decision.get('alternatives', [])
                if alternatives:
                    st.subheader("🔄 Alternative Models")
                    for i, (alt_model, alt_score) in enumerate(alternatives[:3], 1):
                        st.write(f"{i}. {alt_model.value}: {alt_score:.3f}")
                
                # Simulate execution (for demo purposes)
                if st.button("🎭 Simulate Task Execution"):
                    # Simple simulation
                    import random
                    success = random.random() > 0.2  # 80% success rate
                    quality_score = random.uniform(0.6, 1.0)
                    execution_time = random.uniform(15, 120)
                    
                    # Create outcome
                    complexity_obj = TaskComplexity(
                        technical_complexity=complexity_level,
                        novelty=0.3,
                        safety_risk=0.1,
                        context_requirement=0.4,
                        interdependence=0.2,
                        estimated_tokens=task['context']['estimated_tokens'],
                        requires_reasoning=task_type == TaskType.REASONING_LONG.value,
                        requires_creativity=task_type == TaskType.CODE_UI.value,
                        time_sensitive=time_sensitive
                    )
                    
                    outcome = TaskOutcome(
                        task_id=f"demo_{int(datetime.now().timestamp())}",
                        model_used=routing_decision['selected_model'],
                        task_type=TaskType(task_type),
                        complexity=complexity_obj,
                        success=success,
                        quality_score=quality_score,
                        execution_time=execution_time,
                        token_usage=task['context']['estimated_tokens'],
                        cost=task['context']['estimated_tokens'] * 0.002 / 1000,
                        context=task['context'],
                        error_type=None if success else "demo_error",
                        timestamp=datetime.now()
                    )
                    
                    # Update router learning
                    router.update_from_outcome(outcome.task_id, outcome)
                    
                    # Show results
                    result_col1, result_col2 = st.columns([1, 1])
                    with result_col1:
                        st.metric("Success", "✅ Yes" if success else "❌ No")
                        st.metric("Quality Score", f"{quality_score:.3f}")
                    with result_col2:
                        st.metric("Execution Time", f"{execution_time:.1f}s")
                        st.metric("Cost", f"${outcome.cost:.4f}")
                    
                    st.success("Router learning updated with task outcome!")
                
            except Exception as e:
                st.error(f"Error routing task: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    # Performance Analysis
    st.subheader("📈 Performance Analysis")
    
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["Model Performance", "Bandit Learning", "Cost Analysis"])
    
    with analysis_tab1:
        st.markdown("### Model Performance Summary")
        try:
            performance_summary = router.get_model_performance_summary()
            if performance_summary:
                for model_name, task_metrics in performance_summary.items():
                    with st.expander(f"📊 {model_name}"):
                        for task_type, metrics in task_metrics.items():
                            st.markdown(f"**{task_type}:**")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Success Rate", f"{metrics['success_rate']:.3f}")
                            with col2:
                                st.metric("Avg Quality", f"{metrics['avg_quality']:.3f}")
                            with col3:
                                st.metric("Avg Cost", f"${metrics['avg_cost']:.4f}")
                            with col4:
                                st.metric("Sample Count", metrics['sample_count'])
            else:
                st.info("No performance data available. Run some tasks to see analytics.")
        except Exception as e:
            st.error(f"Error loading performance data: {e}")
    
    with analysis_tab2:
        st.markdown("### Thompson Sampling Bandit Statistics")
        try:
            bandit_stats = router.bandit.get_arm_statistics()
            if bandit_stats:
                # Create visualization data
                models = list(bandit_stats.keys())
                means = [stats['estimated_mean'] for stats in bandit_stats.values()]
                pulls = [stats['total_pulls'] for stats in bandit_stats.values()]
                
                # Display statistics
                for model, stats in bandit_stats.items():
                    with st.expander(f"🎰 {model}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Estimated Mean", f"{stats['estimated_mean']:.3f}")
                        with col2:
                            ci_lower, ci_upper = stats['confidence_interval']
                            st.metric("Confidence Interval", f"[{ci_lower:.3f}, {ci_upper:.3f}]")
                        with col3:
                            st.metric("Total Pulls", stats['total_pulls'])
                        
                        st.metric("Alpha (Successes)", f"{stats['alpha']:.2f}")
                        st.metric("Beta (Failures)", f"{stats['beta']:.2f}")
                        st.caption(f"Last updated: {stats['last_updated']}")
            else:
                st.info("No bandit learning data available yet.")
        except Exception as e:
            st.error(f"Error loading bandit statistics: {e}")
    
    with analysis_tab3:
        st.markdown("### Cost Analysis")
        try:
            # Budget overview by complexity
            st.markdown("#### Budget Limits by Project Complexity")
            for complexity in ProjectComplexity:
                budget = router.cost_governor.budgets[complexity]
                with st.expander(f"💰 {complexity.value.title()} Projects"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Max Tokens", f"{budget.max_tokens:,}")
                        st.metric("Max Cost", f"${budget.max_cost_usd}")
                    with col2:
                        st.metric("Max Agents", budget.max_agents)
                        st.metric("Max Requests", budget.max_requests)
                    with col3:
                        st.metric("Time Window", f"{budget.time_window_hours}h")
            
            # Current usage
            st.markdown("#### Current Usage")
            usage_summary = router.cost_governor.get_usage_summary("demo_project")
            if 'error' not in usage_summary and 'current_usage' in usage_summary:
                usage = usage_summary['current_usage']
                budget = usage_summary['budget_limits']
                utilization = usage_summary['utilization']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tokens Used", f"{usage['tokens_used']:,} / {budget['max_tokens']:,}")
                    st.progress(utilization['tokens_percent'] / 100)
                    st.metric("Requests Made", f"{usage['requests_made']} / {budget['max_requests']}")
                    st.progress(utilization['requests_percent'] / 100)
                
                with col2:
                    st.metric("Cost Incurred", f"${usage['cost_incurred']:.2f} / ${budget['max_cost_usd']:.2f}")
                    st.progress(utilization['cost_percent'] / 100)
                    st.metric("Active Agents", usage['agents_active'])
            else:
                st.info("No usage data available yet.")
        except Exception as e:
            st.error(f"Error loading cost analysis: {e}")
    
    # Insights and Recommendations
    st.subheader("🔍 AI Insights and Recommendations")
    
    try:
        insights = router.performance_tracker.generate_insights()
        
        if 'model_recommendations' in insights and insights['model_recommendations']:
            st.markdown("#### 🎯 Recommended Models by Task Type")
            recommendations = insights['model_recommendations']
            for task_type, model in recommendations.items():
                st.write(f"**{task_type}**: {model}")
        
        if 'optimization_opportunities' in insights:
            opportunities = insights['optimization_opportunities'][:5]  # Top 5
            if opportunities:
                st.markdown("#### ⚡ Top Optimization Opportunities")
                for i, opp in enumerate(opportunities, 1):
                    st.write(f"{i}. **{opp['type']}**: {opp['model']} for {opp['task_type']}")
                    st.caption(f"   → {opp['suggestion']}")
        
        if 'summary' in insights and insights['summary']:
            st.markdown("#### 📋 Performance Summary")
            summary = insights['summary']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tasks Analyzed", summary.get('total_tasks_analyzed', 0))
            with col2:
                st.metric("Success Rate", f"{summary.get('overall_success_rate', 0):.3f}")
            with col3:
                st.metric("Total Cost", f"${summary.get('total_cost', 0):.2f}")
    
    except Exception as e:
        st.error(f"Error generating insights: {e}")
        
    # Export/Import Options
    st.subheader("🔄 Data Management")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Learning Data"):
            try:
                learning_data = router.bandit.export_learning_data()
                st.download_button(
                    label="💾 Download Learning Data",
                    data=json.dumps(learning_data, indent=2),
                    file_name=f"router_learning_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Error exporting data: {e}")
    
    with col2:
        if st.button("🧹 Reset Router Learning"):
            if st.confirm("Are you sure you want to reset all learning data?"):
                try:
                    # Reset bandit arms
                    for arm_id in router.bandit.arms.keys():
                        router.bandit.reset_arm(arm_id)
                    
                    # Reset cost usage
                    router.cost_governor.reset_usage("demo_project")
                    
                    st.success("Router learning data has been reset!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error resetting data: {e}")


if __name__ == "__main__":
    main()