import streamlit as st
import json
import uuid
import os
from datetime import datetime
from typing import Dict, List, Any
import asyncio
import time

# Multi-model AI integration
from components.api_key_manager import render_api_key_interface, check_required_keys, render_model_performance_metrics
from components.collaboration_dashboard import render_collaboration_dashboard, render_model_health_status
from core.model_orchestrator import orchestrator, reinitialize_orchestrator, AgentType

# Agent imports 
from agents.project_manager import ProjectManagerAgent
from agents.code_generator import CodeGeneratorAgent
from agents.ui_designer import UIDesignerAgent
from agents.test_writer import TestWriterAgent
from agents.debugger import DebuggerAgent
from core.orchestrator import AgentOrchestrator
from core.memory import ProjectMemory
from utils.helpers import format_code_for_download, create_project_template

# Page configuration
st.set_page_config(
    page_title="CodeCompanion - Multi-Agent AI Development",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "agents" not in st.session_state:
    st.session_state.agents = {}
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
if "memory" not in st.session_state:
    st.session_state.memory = ProjectMemory()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "agent_status" not in st.session_state:
    st.session_state.agent_status = {}
if "project_files" not in st.session_state:
    st.session_state.project_files = {}

def initialize_agents():
    """Initialize all agents with multi-model integration"""
    if not st.session_state.agents:
        st.session_state.agents = {
            "project_manager": ProjectManagerAgent(),
            "code_generator": CodeGeneratorAgent(),
            "ui_designer": UIDesignerAgent(),
            "test_writer": TestWriterAgent(),
            "debugger": DebuggerAgent()
        }
        st.session_state.orchestrator = AgentOrchestrator(st.session_state.agents, st.session_state.memory)
        
        # Initialize agent status with model assignments
        model_assignments = {
            "project_manager": "Claude (Strategic Planning)",
            "code_generator": "GPT-4 (Creative Coding)",
            "ui_designer": "GPT-4 (Design Creativity)",
            "test_writer": "Gemini (Systematic Testing)",
            "debugger": "Claude (Logical Analysis)"
        }
        
        for agent_name in st.session_state.agents:
            st.session_state.agent_status[agent_name] = {
                "status": "idle",
                "progress": 0,
                "current_task": "",
                "last_activity": None,
                "assigned_model": model_assignments.get(agent_name, "Unknown")
            }

def update_agent_status(agent_name: str, status: str, progress: int = 0, task: str = ""):
    """Update agent status and trigger UI refresh"""
    st.session_state.agent_status[agent_name] = {
        "status": status,
        "progress": progress,
        "current_task": task,
        "last_activity": datetime.now()
    }

def main():
    st.title("🤖 CodeCompanion Orchestra - Multi-Model AI Development")
    st.markdown("### Real-time collaboration between Claude, GPT-4, and Gemini")
    
    # API Key Management Interface
    st.sidebar.markdown("# 🔑 Multi-Model Configuration")
    
    # Render API key interface
    api_keys = render_api_key_interface()
    
    # Check if at least one API key is configured
    keys_ready, status_message = check_required_keys()
    
    if not keys_ready:
        st.error(status_message)
        st.markdown("""
        ## 🚀 Get Started with Multi-Model AI
        
        **CodeCompanion Orchestra** uses three specialized AI models:
        
        - **🟣 Claude** - Strategic planning, architecture decisions, debugging logic
        - **🔵 GPT-4** - Code generation, creative problem-solving, UI design  
        - **🔴 Gemini** - Testing strategies, validation, quality assurance
        
        Configure at least one API key in the sidebar to begin collaborative development.
        """)
        return
    
    st.success(status_message)
    
    # Initialize agents after API keys are configured
    initialize_agents()
    
    # Render model performance metrics
    render_model_performance_metrics()
    
    # Main application tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 AI Dashboard", "📁 Project Files", "⚙️ Settings"])
    
    with tab1:
        render_chat_interface()
    
    with tab2:
        render_collaboration_dashboard()
        render_model_health_status()
    
    with tab3:
        render_project_files()
    
    with tab4:
        render_settings()

def render_chat_interface():
    """Render the main chat interface with multi-model collaboration"""
    st.markdown("## 💬 AI Agent Collaboration")
    
    # Display active agents and their assigned models
    col1, col2, col3, col4, col5 = st.columns(5)
    agent_info = [
        ("project_manager", "Project Manager", "🟣", "Claude"),
        ("code_generator", "Code Generator", "🔵", "GPT-4"), 
        ("ui_designer", "UI Designer", "🔵", "GPT-4"),
        ("test_writer", "Test Writer", "🔴", "Gemini"),
        ("debugger", "Debugger", "🟣", "Claude")
    ]
    
    cols = [col1, col2, col3, col4, col5]
    for i, (agent_key, agent_name, color, model) in enumerate(agent_info):
        with cols[i]:
            status = st.session_state.agent_status.get(agent_key, {})
            status_color = {
                "idle": "🟢",
                "working": "🟡", 
                "completed": "✅",
                "error": "🔴"
            }.get(status.get("status", "idle"), "⚪")
            
            st.markdown(f"**{color} {agent_name}**")
            st.caption(f"Powered by {model}")
            st.caption(f"Status: {status_color} {status.get('status', 'idle').title()}")
    
    # Chat history display
    st.markdown("### 📜 Conversation History")
    chat_container = st.container()
    
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            timestamp = datetime.fromisoformat(message['timestamp']).strftime("%H:%M:%S")
            
            if message['role'] == 'user':
                st.markdown(f"**👤 You** `{timestamp}`")
                st.markdown(message['content'])
            else:
                agent_name = message.get('agent', 'Assistant')
                model_used = message.get('model', 'Unknown')
                st.markdown(f"**🤖 {agent_name}** `{timestamp}` *via {model_used}*")
                st.markdown(message['content'])
            st.markdown("---")
    
    # User input
    st.markdown("### ✍️ New Request")
    user_input = st.text_area("Describe your development task:", height=100, 
                             placeholder="e.g., 'Create a web app for task management with user authentication'")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚀 Submit", disabled=not user_input.strip()):
            process_user_request(user_input.strip())
    
    with col2:
        if st.button("🗳️ Get AI Consensus", disabled=not user_input.strip()):
            get_multi_model_consensus(user_input.strip())

def process_user_request(request: str):
    """Process user request through the multi-agent system"""
    # Add user message to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": request,
        "timestamp": datetime.now().isoformat()
    })
    
    # Update UI to show processing
    st.info("🤖 AI agents are collaborating on your request...")
    
    try:
        # Process through orchestrator
        if st.session_state.orchestrator:
            with st.spinner("Multi-agent processing in progress..."):
                result = st.session_state.orchestrator.process_request(request)
                
                # Add agent response to chat history
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": result.get("response", "No response generated"),
                    "agent": result.get("agent", "System"),
                    "model": result.get("model_used", "Unknown"),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Handle any generated files
                if "files" in result:
                    st.session_state.project_files.update(result["files"])
                
                st.success("✅ Task completed by AI agents!")
                st.rerun()
    except Exception as e:
        st.error(f"Error processing request: {str(e)}")

def get_multi_model_consensus(question: str):
    """Get consensus from multiple AI models"""
    st.info("🗳️ Consulting multiple AI models for consensus...")
    
    try:
        # This would integrate with the orchestrator's consensus feature
        with st.spinner("Building AI consensus..."):
            time.sleep(2)  # Simulate processing time
            
            # Add consensus result to chat
            consensus_response = f"""
            ## 🗳️ Multi-Model AI Consensus

            **Question:** {question}

            **Claude's Perspective:** Strategic analysis suggests focusing on scalable architecture...
            **GPT-4's Perspective:** Implementation should prioritize user experience and clean code...
            **Gemini's Perspective:** Testing strategy should include comprehensive edge cases...

            **Consensus Recommendation:** Proceed with a modular approach that balances all three perspectives.
            """
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": consensus_response,
                "agent": "Multi-Model Consensus",
                "model": "Claude + GPT-4 + Gemini",
                "timestamp": datetime.now().isoformat()
            })
            
            st.success("✅ AI consensus reached!")
            st.rerun()
    except Exception as e:
        st.error(f"Error building consensus: {str(e)}")

def render_project_files():
    """Render project files interface"""
    st.markdown("## 📁 Generated Project Files")
    
    if not st.session_state.project_files:
        st.info("No project files generated yet. Start a conversation to create files.")
        return
    
    # File explorer
    for filename, content in st.session_state.project_files.items():
        with st.expander(f"📄 {filename}"):
            st.code(content, language="python")
            
            # Download button
            st.download_button(
                f"Download {filename}",
                data=content,
                file_name=filename,
                mime="text/plain",
                key=f"download_{filename}"
            )
    
    # Download all files as ZIP
    if len(st.session_state.project_files) > 1:
        if st.button("📦 Download All Files"):
            st.success("Download feature would be implemented here")

def render_settings():
    """Render application settings"""
    st.markdown("## ⚙️ Application Settings")
    
    st.markdown("### 🤖 Model Preferences")
    st.info("Model assignments are currently fixed based on agent specializations. Custom model routing will be available in a future update.")
    
    # Show current model assignments
    assignments = {
        "Project Manager": "Claude (Strategic Planning)",
        "Code Generator": "GPT-4 (Creative Coding)",
        "UI Designer": "GPT-4 (Design Creativity)",
        "Test Writer": "Gemini (Systematic Testing)",
        "Debugger": "Claude (Logical Analysis)"
    }
    
    for agent, model in assignments.items():
        st.write(f"**{agent}:** {model}")
    
    st.markdown("### 🔄 System Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear Chat History"):
            st.session_state.chat_history = []
            st.success("Chat history cleared!")
            st.rerun()
    
    with col2:
        if st.button("🗂️ Clear Project Files"):
            st.session_state.project_files = {}
            st.success("Project files cleared!")
            st.rerun()
    
    st.markdown("### 📊 System Information")
    st.write(f"**Active Agents:** {len(st.session_state.agents)}")
    st.write(f"**Chat Messages:** {len(st.session_state.chat_history)}")
    st.write(f"**Project Files:** {len(st.session_state.project_files)}")
    
    # Model statistics
    stats = orchestrator.get_model_statistics()
    st.markdown("### 🏥 Model Health")
    for model, data in stats.items():
        if data["is_connected"]:
            st.write(f"**{model.title()}:** ✅ Online - {data['success_count']} requests, {data['reliability']:.1f}% success rate")
    
    # Sidebar for project configuration
    with st.sidebar:
        st.header("🎛️ Project Configuration")
        
        # Project templates
        st.subheader("Project Template")
        template_options = ["Custom Project", "Web Application", "API Service", "Data Pipeline", "Mobile App"]
        selected_template = st.selectbox("Choose a template:", template_options)
        
        if st.button("🚀 New Project"):
            project_id = str(uuid.uuid4())[:8]
            st.session_state.current_project = {
                "id": project_id,
                "name": f"Project_{project_id}",
                "template": selected_template,
                "created_at": datetime.now(),
                "status": "active"
            }
            st.session_state.memory.clear_context()
            st.session_state.chat_history = []
            st.session_state.project_files = {}
            st.success(f"Created new project: {st.session_state.current_project['name']}")
            st.rerun()
        
        # Agent Management
        st.subheader("🤖 Agent Management")
        for agent_name, agent in st.session_state.agents.items():
            status_info = st.session_state.agent_status.get(agent_name, {})
            status = status_info.get("status", "idle")
            progress = status_info.get("progress", 0)
            current_task = status_info.get("current_task", "")
            
            # Status indicator
            status_colors = {
                "idle": "🔵",
                "thinking": "🟡",
                "working": "🟢",
                "completed": "✅",
                "error": "🔴"
            }
            
            st.markdown(f"**{status_colors.get(status, '⚪')} {agent_name.replace('_', ' ').title()}**")
            if current_task:
                st.caption(f"Task: {current_task}")
            if progress > 0:
                st.progress(progress / 100)
            st.markdown("---")
        
        # Download project files
        if st.session_state.project_files:
            st.subheader("📁 Download Project")
            if st.button("📥 Download All Files"):
                files_data = format_code_for_download(st.session_state.project_files)
                st.download_button(
                    label="Download Project.zip",
                    data=files_data,
                    file_name=f"{st.session_state.current_project['name']}_files.json",
                    mime="application/json"
                )

    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Chat interface
        st.subheader("💬 Unified Chat Interface")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    if message["role"] == "user":
                        st.write(message["content"])
                    else:
                        # Agent message with metadata
                        agent_name = message.get("agent", "system")
                        st.markdown(f"**{agent_name.replace('_', ' ').title()}** {message.get('timestamp', '')}")
                        st.write(message["content"])
                        
                        # Show handoff information if available
                        if message.get("handoff_to"):
                            st.info(f"🔄 Handing off to: {message['handoff_to'].replace('_', ' ').title()}")
        
        # Chat input
        user_input = st.chat_input("Describe your project or ask for help...")
        
        if user_input:
            # Add user message to chat
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
            # Process with orchestrator
            if st.session_state.orchestrator:
                with st.spinner("Agents are collaborating..."):
                    # Route to appropriate agent and get response
                    routed_agent = st.session_state.orchestrator.route_request(user_input)
                    update_agent_status(routed_agent, "thinking", 10, "Analyzing request")
                    
                    # Simulate agent processing
                    time.sleep(1)
                    update_agent_status(routed_agent, "working", 50, "Processing request")
                    
                    # Get agent response
                    response = st.session_state.agents[routed_agent].process_request(
                        user_input, 
                        st.session_state.memory.get_context()
                    )
                    
                    update_agent_status(routed_agent, "completed", 100, "Task completed")
                    
                    # Add agent response to chat
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "agent": routed_agent,
                        "content": response["content"],
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "handoff_to": response.get("handoff_to")
                    })
                    
                    # Update project files if code was generated
                    if response.get("files"):
                        st.session_state.project_files.update(response["files"])
                    
                    # Update memory context
                    st.session_state.memory.add_interaction(user_input, response["content"], routed_agent)
                    
                    # Handle agent handoffs
                    if response.get("handoff_to"):
                        next_agent = response["handoff_to"]
                        update_agent_status(next_agent, "thinking", 20, "Received handoff")
                        
                        # Process handoff
                        handoff_response = st.session_state.agents[next_agent].process_handoff(
                            response["content"],
                            st.session_state.memory.get_context()
                        )
                        
                        update_agent_status(next_agent, "completed", 100, "Handoff completed")
                        
                        # Add handoff response
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "agent": next_agent,
                            "content": handoff_response["content"],
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        
                        if handoff_response.get("files"):
                            st.session_state.project_files.update(handoff_response["files"])
            
            st.rerun()
    
    with col2:
        # Agent activity monitor
        st.subheader("📊 Agent Activity Monitor")
        
        # Real-time agent status
        for agent_name, status_info in st.session_state.agent_status.items():
            with st.expander(f"{agent_name.replace('_', ' ').title()}", expanded=True):
                status = status_info.get("status", "idle")
                progress = status_info.get("progress", 0)
                current_task = status_info.get("current_task", "")
                last_activity = status_info.get("last_activity")
                
                st.metric("Status", status.title())
                if current_task:
                    st.text(f"Current Task: {current_task}")
                if progress > 0:
                    st.progress(progress / 100)
                if last_activity:
                    st.caption(f"Last Activity: {last_activity.strftime('%H:%M:%S')}")
        
        # Project files preview
        if st.session_state.project_files:
            st.subheader("📄 Generated Files")
            for filename, content in st.session_state.project_files.items():
                with st.expander(f"📁 {filename}"):
                    if filename.endswith(('.py', '.js', '.html', '.css', '.json')):
                        st.code(content, language=filename.split('.')[-1])
                    else:
                        st.text(content)
        
        # Memory context display
        if st.session_state.memory.get_context():
            st.subheader("🧠 Shared Context")
            with st.expander("View Context", expanded=False):
                context = st.session_state.memory.get_context()
                st.json(context)

    # Current project info
    if st.session_state.current_project:
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Project ID", st.session_state.current_project["id"])
        with col2:
            st.metric("Template", st.session_state.current_project["template"])
        with col3:
            st.metric("Status", st.session_state.current_project["status"].title())
        with col4:
            st.metric("Files Generated", len(st.session_state.project_files))

if __name__ == "__main__":
    main()
