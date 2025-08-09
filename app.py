import streamlit as st
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any
import asyncio
import time
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
    """Initialize all agents and orchestrator"""
    if not st.session_state.agents:
        st.session_state.agents = {
            "project_manager": ProjectManagerAgent(),
            "code_generator": CodeGeneratorAgent(),
            "ui_designer": UIDesignerAgent(),
            "test_writer": TestWriterAgent(),
            "debugger": DebuggerAgent()
        }
        st.session_state.orchestrator = AgentOrchestrator(st.session_state.agents, st.session_state.memory)
        
        # Initialize agent status
        for agent_name in st.session_state.agents:
            st.session_state.agent_status[agent_name] = {
                "status": "idle",
                "progress": 0,
                "current_task": "",
                "last_activity": None
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
    st.title("🤖 CodeCompanion - Multi-Agent AI Development System")
    st.markdown("### Live collaboration between specialized AI agents")
    
    initialize_agents()
    
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
