import streamlit as st
import json
import uuid
import os
from datetime import datetime
from typing import Dict, List, Any
import asyncio
import time

# Core system components
from components.collaboration_dashboard import render_collaboration_dashboard, render_model_health_status
from core.model_orchestrator import AgentType
from core.workflow_orchestrator import WorkflowOrchestrator, ProjectType, ProjectComplexity

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

# Initialize session state with comprehensive error handling
from utils.session_manager import init_session_safely, get_session_value, set_session_value, session_manager, validate_session, cleanup_session, partial_reset, emergency_reset
from utils.error_handler import log_user_action, logger

# Initialize session safely
try:
    if not init_session_safely():
        st.error("Failed to initialize session. Please refresh the page.")
        st.stop()
except Exception as e:
    logger.error(f"Critical error during session initialization: {str(e)}")
    st.error("Critical initialization error. Please refresh the page and try again.")
    st.stop()

def initialize_agents():
    """Initialize all agents with comprehensive error handling"""
    from utils.error_handler import safe_api_call, logger
    from utils.session_manager import session_manager
    
    try:
        # Check if already initialized
        if get_session_value('agents') and get_session_value('orchestrator'):
            return True
        
        # Initialize through session manager (it handles errors internally)
        session_manager._initialize_agents_safely()
        
        log_user_action("agents_initialized", {"success": True})
        return True
        
    except Exception as e:
        logger.error(f"Critical error initializing agents: {str(e)}")
        st.error("Failed to initialize AI agents. Please refresh the page.")
        log_user_action("agents_initialization_failed", {"error": str(e)})
        return False

def update_agent_status(agent_name: str, status: str, progress: int = 0, task: str = ""):
    """Update agent status with comprehensive error handling"""
    from utils.error_handler import logger
    
    try:
        # Validate inputs
        if not agent_name or not isinstance(agent_name, str):
            logger.warning(f"Invalid agent name: {agent_name}")
            return False
            
        if not isinstance(progress, int) or progress < 0 or progress > 100:
            progress = max(0, min(100, int(progress))) if isinstance(progress, (int, float)) else 0
        
        # Get current agent status safely
        agent_status = get_session_value('agent_status', {})
        
        # Update status
        agent_status[agent_name] = {
            "status": str(status),
            "progress": progress,
            "current_task": str(task)[:200],  # Limit task description length
            "last_activity": datetime.now()
        }
        
        # Save back to session state
        set_session_value('agent_status', agent_status)
        
        log_user_action("agent_status_updated", {
            "agent": agent_name, 
            "status": status, 
            "progress": progress
        })
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating agent status for {agent_name}: {str(e)}")
        return False

def main():
    """Main application with comprehensive error handling and stability measures"""
    from utils.error_handler import log_user_action, get_error_help_message
    from utils.session_manager import validate_session, cleanup_session, emergency_reset, partial_reset, session_manager
    
    try:
        st.title("🤖 CodeCompanion - Multi-Agent AI Development System")
        st.markdown("### Live collaboration between specialized AI agents")
        
        # Add emergency controls and API health monitoring in sidebar
        with st.sidebar:
            render_emergency_controls()
            st.markdown("---")
            render_sidebar_health_status()
        
        # Validate session state
        validation_results = validate_session()
        failed_validations = [k for k, v in validation_results.items() if not v]
        
        if failed_validations:
            st.warning(f"Session validation issues detected: {', '.join(failed_validations)}")
            if st.button("🔧 Fix Session Issues"):
                partial_reset()
                st.rerun()
        
        # Initialize agents with error handling
        if not initialize_agents():
            st.error("Failed to initialize AI agents. Please try the emergency reset.")
            return
        
        # Periodic memory cleanup
        if get_session_value('error_count', 0) > 5:
            cleanup_session()
            session_manager.increment_error_count()
        
        # Check if we have an active orchestrated project
        active_project = get_session_value('active_project')
        if active_project:
            render_live_orchestration_dashboard()
        else:
            render_project_initiation_panel()
            
        log_user_action("main_page_rendered", {"active_project": bool(active_project)})
        
    except Exception as e:
        logger.error(f"Critical error in main(): {str(e)}")
        session_manager.increment_error_count()
        
        st.error("A critical error occurred. Please use the emergency controls.")
        st.exception(e)
        
        # Show emergency controls prominently
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Partial Reset", type="primary"):
                partial_reset()
                st.rerun()
        with col2:
            if st.button("🚨 Emergency Reset", type="secondary"):
                emergency_reset()
                st.rerun()
        with col3:
            if st.button("🧹 Clear Memory"):
                cleanup_session()
                st.rerun()

def render_emergency_controls():
    """Render emergency controls in sidebar"""
    
    st.markdown("## 🚨 Emergency Controls")
    
    # Session health check
    session_info = session_manager.get_session_info()
    error_count = session_info.get('error_count', 0)
    
    if error_count > 0:
        st.warning(f"Errors detected: {error_count}")
    else:
        st.success("Session healthy")
    
    # Emergency buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Partial Reset", help="Reset problematic state while keeping chat history"):
            partial_reset()
            st.success("Partial reset completed")
            st.rerun()
    
    with col2:
        if st.button("🚨 Full Reset", help="Complete session reset (clears everything)"):
            emergency_reset()
            st.success("Emergency reset completed")
            st.rerun()
    
    if st.button("🧹 Memory Cleanup", help="Clean up old data to free memory"):
        cleanup_session()
        st.success("Memory cleanup completed")
        st.rerun()
    
    # Session info expander
    with st.expander("📊 Session Info", expanded=False):
        for key, value in session_info.items():
            st.text(f"{key}: {value}")
    
    # Validation status
    with st.expander("🔍 Validation Status", expanded=False):
        validation_results = validate_session()
        for key, valid in validation_results.items():
            status = "✅" if valid else "❌"
            st.text(f"{status} {key}")
    
    # Main navigation tabs - restored all missing tabs
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💬 Chat Interface", 
        "🎼 Live Orchestra", 
        "🏥 System Health",
        "📊 Collaboration Dashboard",
        "📁 Project Files",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_chat_interface()
    
    with tab2:
        if st.session_state.workflow_orchestrator and st.session_state.active_project:
            render_live_orchestration()
        else:
            render_project_initiation_panel()
    
    with tab3:
        render_system_health()
    
    with tab4:
        render_collaboration_dashboard()
    
    with tab5:
        render_project_files()
    
    with tab6:
        render_settings()

def render_chat_interface():
    """Render the main chat interface with multi-model collaboration"""
    st.markdown("## 💬 AI Agent Collaboration")
    
    # Display active agents
    col1, col2, col3, col4, col5 = st.columns(5)
    agent_info = [
        ("project_manager", "Project Manager", "📋"),
        ("code_generator", "Code Generator", "💻"), 
        ("ui_designer", "UI Designer", "🎨"),
        ("test_writer", "Test Writer", "🧪"),
        ("debugger", "Debugger", "🔍")
    ]
    
    cols = [col1, col2, col3, col4, col5]
    for i, (agent_key, agent_name, icon) in enumerate(agent_info):
        with cols[i]:
            status = st.session_state.agent_status.get(agent_key, {})
            status_color = {
                "idle": "🟢",
                "working": "🟡", 
                "completed": "✅",
                "error": "🔴"
            }.get(status.get("status", "idle"), "⚪")
            
            st.markdown(f"**{icon} {agent_name}**")
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
                st.markdown(f"**🤖 {agent_name}** `{timestamp}`")
                st.markdown(message['content'])
            st.markdown("---")
    
    # User input with enhanced safety
    st.markdown("### ✍️ New Request")
    
    # Input validation info
    st.caption("💡 Tip: Be specific and clear. Max 5000 characters.")
    
    user_input = st.text_area(
        "Describe your development task:", 
        height=100, 
        max_chars=5000,
        placeholder="e.g., 'Create a web app for task management with user authentication'",
        help="Describe what you want to build. The AI agents will collaborate to create it."
    )
    
    # Character count
    if user_input:
        char_count = len(user_input)
        if char_count > 4000:
            st.warning(f"Input length: {char_count}/5000 characters (getting close to limit)")
        else:
            st.caption(f"Characters: {char_count}/5000")
    
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        submit_disabled = not user_input.strip() or len(user_input.strip()) < 10
        if st.button("🚀 Submit", 
                    disabled=submit_disabled,
                    help="Submit your request to the AI agents"):
            if process_user_request(user_input.strip()):
                st.balloons()
    
    with col2:
        consensus_disabled = not user_input.strip() or len(user_input.strip()) < 10
        if st.button("🤝 Get Team Consensus", 
                    disabled=consensus_disabled,
                    help="Get input from multiple AI agents before proceeding"):
            get_agent_consensus(user_input.strip())
    
    with col3:
        # Emergency stop button
        if st.button("⏹️ Stop All Operations", 
                    type="secondary",
                    help="Emergency stop for all running operations"):
            emergency_stop_operations()

def process_user_request(request: str):
    """Process user request with comprehensive error handling and stability measures"""
    from utils.error_handler import validate_input, safe_api_call, get_error_help_message, log_user_action
    from utils.session_manager import session_manager
    
    try:
        # Validate input
        validation = validate_input(request, max_length=5000)
        if not validation['valid']:
            st.error(f"Input validation failed: {validation['error']}")
            return False
        
        sanitized_request = validation['sanitized']
        
        # Add user message to chat history safely
        chat_history = get_session_value('chat_history', [])
        
        # Limit chat history length
        if len(chat_history) > 100:
            chat_history = chat_history[-100:]
            set_session_value('chat_history', chat_history)
        
        chat_history.append({
            "role": "user",
            "content": sanitized_request,
            "timestamp": datetime.now().isoformat()
        })
        set_session_value('chat_history', chat_history)
        
        log_user_action("user_request_submitted", {"request_length": len(sanitized_request)})
        
        # Show progress with timeout
        progress_container = st.empty()
        progress_container.info("🤖 AI agents are collaborating on your request...")
        
        # Get orchestrator safely
        orchestrator = get_session_value('orchestrator')
        if not orchestrator:
            st.error("AI system not ready. Please refresh the page.")
            session_manager.increment_error_count()
            return False
        
        # Process with timeout and error handling
        def _process_request():
            return orchestrator.process_request(sanitized_request)
        
        result = safe_api_call(
            _process_request,
            service_name="orchestrator_process",
            timeout=45  # 45 second timeout
        )
        
        progress_container.empty()
        
        if result['success']:
            response_data = result.get('data', {})
            
            # Add agent response to chat history
            chat_history.append({
                "role": "assistant", 
                "content": response_data.get("response", result.get('content', "Task completed successfully")),
                "agent": response_data.get("agent", "System"),
                "model": response_data.get("model_used", "Unknown"),
                "timestamp": datetime.now().isoformat()
            })
            set_session_value('chat_history', chat_history)
            
            # Handle any generated files safely
            if "files" in response_data and response_data["files"]:
                project_files = get_session_value('project_files', {})
                project_files.update(response_data["files"])
                set_session_value('project_files', project_files)
            
            st.success("✅ Task completed by AI agents!")
            log_user_action("user_request_completed", {"success": True})
            st.rerun()
            return True
            
        else:
            error_type = result.get('error_type', 'unknown')
            error_help = get_error_help_message(error_type)
            
            st.error(f"Processing failed: {error_help}")
            
            # Add error message to chat
            chat_history.append({
                "role": "assistant", 
                "content": f"I encountered an error: {error_help}",
                "agent": "System",
                "error": True,
                "timestamp": datetime.now().isoformat()
            })
            set_session_value('chat_history', chat_history)
            
            session_manager.increment_error_count()
            log_user_action("user_request_failed", {"error_type": error_type})
            return False
            
    except Exception as e:
        logger.error(f"Critical error processing user request: {str(e)}")
        session_manager.increment_error_count()
        
        st.error("A critical error occurred while processing your request.")
        st.info("Please try:")
        st.info("1. Using simpler language")
        st.info("2. Breaking your request into smaller parts") 
        st.info("3. Using the 'Clear Chat History' button")
        st.info("4. Refreshing the page if problems persist")
        
        log_user_action("user_request_critical_error", {"error": str(e)})
        return False

def get_agent_consensus(question: str):
    """Get consensus from multiple agents with comprehensive error handling"""
    from utils.error_handler import validate_input, safe_api_call, log_user_action
    from utils.session_manager import session_manager
    
    try:
        # Validate input
        validation = validate_input(question, max_length=2000)
        if not validation['valid']:
            st.error(f"Input validation failed: {validation['error']}")
            return False
        
        sanitized_question = validation['sanitized']
        log_user_action("consensus_requested", {"question_length": len(sanitized_question)})
        
        st.info("🤝 Consulting agent team for consensus...")
        
        # Get agents safely
        agents = get_session_value('agents', {})
        if len(agents) < 3:
            st.error("Not enough AI agents available. Please refresh the page.")
            return False
        
        progress_bar = st.progress(0)
        consensus_container = st.empty()
        
        def _build_consensus():
            # Simulate consensus building with multiple agents
            responses = {}
            agent_names = list(agents.keys())[:4]  # Limit to 4 agents for consensus
            
            for i, agent_name in enumerate(agent_names):
                try:
                    agent = agents[agent_name]
                    response = agent.process_request(f"Provide your expert opinion on: {sanitized_question}")
                    responses[agent_name] = response.get('content', 'No response')
                    
                    progress_bar.progress((i + 1) / len(agent_names))
                    consensus_container.info(f"Getting input from {agent_name.replace('_', ' ').title()}...")
                    
                except Exception as e:
                    logger.warning(f"Error getting consensus from {agent_name}: {str(e)}")
                    responses[agent_name] = f"Unable to get response from {agent_name}"
            
            return responses
        
        result = safe_api_call(
            _build_consensus,
            service_name="agent_consensus",
            timeout=60
        )
        
        progress_bar.empty()
        consensus_container.empty()
        
        if result['success']:
            responses = result.get('data', {})
            
            # Format consensus response
            consensus_response = f"## 🤝 Agent Team Consensus\n\n**Question:** {sanitized_question}\n\n"
            
            for agent_name, response in responses.items():
                agent_title = agent_name.replace('_', ' ').title()
                preview = response[:200] + "..." if len(response) > 200 else response
                consensus_response += f"**{agent_title}:** {preview}\n\n"
            
            consensus_response += "**Team Recommendation:** Based on the above analysis, proceed with a collaborative approach that combines the strengths of each perspective."
            
            # Add to chat history
            chat_history = get_session_value('chat_history', [])
            chat_history.append({
                "role": "assistant",
                "content": consensus_response,
                "agent": "Agent Team Consensus",
                "timestamp": datetime.now().isoformat()
            })
            set_session_value('chat_history', chat_history)
            
            st.success("✅ Team consensus reached!")
            log_user_action("consensus_completed", {"success": True})
            st.rerun()
            return True
            
        else:
            error_help = get_error_help_message(result.get('error_type', 'unknown'))
            st.error(f"Consensus building failed: {error_help}")
            session_manager.increment_error_count()
            log_user_action("consensus_failed", {"error_type": result.get('error_type')})
            return False
            
    except Exception as e:
        logger.error(f"Critical error building consensus: {str(e)}")
        session_manager.increment_error_count()
        st.error("Unable to build consensus. Please try again or refresh the page.")
        log_user_action("consensus_critical_error", {"error": str(e)})
        return False

def emergency_stop_operations():
    """Emergency stop for all running operations"""
    try:
        # Clear any running operations
        set_session_value('workflow_status', 'stopped')
        
        # Reset agent statuses
        agent_status = get_session_value('agent_status', {})
        for agent_name in agent_status:
            agent_status[agent_name]['status'] = 'stopped'
            agent_status[agent_name]['current_task'] = 'Operation stopped by user'
        set_session_value('agent_status', agent_status)
        
        st.warning("🛑 All operations have been stopped.")
        log_user_action("emergency_stop", {"success": True})
        
    except Exception as e:
        logger.error(f"Error during emergency stop: {str(e)}")
        st.error("Error stopping operations. Please use the emergency reset.")
        log_user_action("emergency_stop_failed", {"error": str(e)})

def render_project_files():
    """Render project files interface with enhanced functionality"""
    st.markdown("## 📁 Generated Project Files")
    
    project_files = get_session_value('project_files', {})
    
    if not project_files:
        st.info("No project files generated yet. Start a conversation to create files.")
        return
    
    # File statistics
    total_files = len(project_files)
    total_size = sum(len(str(content)) for content in project_files.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", total_files)
    with col2:
        st.metric("Total Size", f"{total_size/1000:.1f} KB")
    with col3:
        if st.button("🗑️ Clear All Files"):
            set_session_value('project_files', {})
            st.success("All files cleared!")
            st.rerun()
    
    # File explorer with improved interface
    for filename, content in project_files.items():
        with st.expander(f"📄 {filename} ({len(str(content))} chars)"):
            # Detect file type for syntax highlighting
            if filename.endswith('.py'):
                language = 'python'
            elif filename.endswith('.js'):
                language = 'javascript'
            elif filename.endswith('.html'):
                language = 'html'
            elif filename.endswith('.css'):
                language = 'css'
            elif filename.endswith('.json'):
                language = 'json'
            else:
                language = 'text'
            
            st.code(content, language=language)
            
            # File actions
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                st.download_button(
                    f"📥 Download {filename}",
                    data=content,
                    file_name=filename,
                    mime="text/plain",
                    key=f"download_{filename}"
                )
            with action_col2:
                if st.button(f"🗑️ Delete", key=f"delete_{filename}"):
                    del project_files[filename]
                    set_session_value('project_files', project_files)
                    st.success(f"Deleted {filename}")
                    st.rerun()
    
    # Download all files as ZIP (enhanced version)
    if total_files > 1:
        if st.button("📦 Download All Files as ZIP"):
            try:
                import zipfile
                import io
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, content in project_files.items():
                        zip_file.writestr(filename, content)
                
                st.download_button(
                    "📥 Download project.zip",
                    data=zip_buffer.getvalue(),
                    file_name="project.zip",
                    mime="application/zip"
                )
            except Exception as e:
                st.error(f"Error creating ZIP file: {str(e)}")

def render_model_health_status():
    """Render AI model health monitoring with real-time API testing"""
    from utils.error_handler import safe_api_call, logger
    
    st.markdown("## 🏥 Model Health Status")
    
    # API status tracking
    api_status = get_session_value('api_status', {
        'openai': {'status': 'unknown', 'last_test': None, 'error': None},
        'anthropic': {'status': 'unknown', 'last_test': None, 'error': None},
        'google': {'status': 'unknown', 'last_test': None, 'error': None}
    })
    
    # Display status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = api_status.get('openai', {})
        icon = "🟢" if status.get('status') == 'healthy' else "🔴" if status.get('status') == 'error' else "🟡"
        st.metric("OpenAI GPT-4", f"{icon} {status.get('status', 'unknown').title()}")
        if status.get('error'):
            with st.expander("🔍 View OpenAI Error", expanded=False):
                st.text(status['error'])
                if status.get('last_test'):
                    st.caption(f"Last tested: {status['last_test']}")
    
    with col2:
        status = api_status.get('anthropic', {})
        icon = "🟢" if status.get('status') == 'healthy' else "🔴" if status.get('status') == 'error' else "🟡"
        st.metric("Claude Sonnet", f"{icon} {status.get('status', 'unknown').title()}")
        if status.get('error'):
            with st.expander("🔍 View Claude Error", expanded=False):
                st.text(status['error'])
                if status.get('last_test'):
                    st.caption(f"Last tested: {status['last_test']}")
    
    with col3:
        status = api_status.get('google', {})
        icon = "🟢" if status.get('status') == 'healthy' else "🔴" if status.get('status') == 'error' else "🟡"
        st.metric("Gemini Flash", f"{icon} {status.get('status', 'unknown').title()}")
        if status.get('error'):
            with st.expander("🔍 View Gemini Error", expanded=False):
                st.text(status['error'])
                if status.get('last_test'):
                    st.caption(f"Last tested: {status['last_test']}")
    
    # Test APIs button
    if st.button("🔍 Test All APIs", help="Test connections to all AI services"):
        with st.spinner("Testing API connections..."):
            test_results = test_all_apis()
            set_session_value('api_status', test_results)
            st.rerun()
    
    # Performance metrics
    with st.expander("📊 Performance Metrics", expanded=False):
        metrics = get_session_value('api_metrics', {})
        if metrics:
            for service, data in metrics.items():
                st.write(f"**{service.title()}:**")
                st.write(f"- Success Rate: {data.get('success_rate', 'N/A')}%")
                st.write(f"- Avg Response Time: {data.get('avg_response_time', 'N/A')}ms")
                st.write(f"- Total Requests: {data.get('total_requests', 0)}")
                st.write("---")
        else:
            st.info("No performance data available yet.")

def test_all_apis():
    """Test all API connections and return status"""
    from utils.error_handler import safe_api_call, logger
    import os
    from datetime import datetime
    
    results = {}
    
    # Test OpenAI
    def test_openai():
        import openai
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception("OPENAI_API_KEY environment variable not set")
        
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        return response.choices[0].message.content
    
    # Test Anthropic
    def test_anthropic():
        import anthropic
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise Exception("ANTHROPIC_API_KEY environment variable not set")
        
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        return response.content[0].text if response.content else "No response"
    
    # Test Google
    def test_google():
        try:
            import google.generativeai as genai
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise Exception("GOOGLE_API_KEY environment variable not set")
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content("Hello")
            return response.text
        except ImportError:
            raise Exception("Google Generative AI library not available. Install with: pip install google-generativeai")
    
    # Test each API
    for api_name, test_func in [
        ('openai', test_openai),
        ('anthropic', test_anthropic), 
        ('google', test_google)
    ]:
        result = safe_api_call(test_func, timeout=15)
        
        if result['success']:
            results[api_name] = {
                'status': 'healthy',
                'last_test': datetime.now().isoformat(),
                'error': None
            }
        else:
            results[api_name] = {
                'status': 'error',
                'last_test': datetime.now().isoformat(),
                'error': result.get('error', 'Unknown error')
            }
    
    return results

def render_sidebar_health_status():
    """Render compact API health status in sidebar"""
    st.markdown("## 🏥 Model Health")
    
    # Get API status
    api_status = get_session_value('api_status', {
        'openai': {'status': 'unknown'},
        'anthropic': {'status': 'unknown'},
        'google': {'status': 'unknown'}
    })
    
    # Compact status display
    for api_name, status in api_status.items():
        status_val = status.get('status', 'unknown')
        icon = "🟢" if status_val == 'healthy' else "🔴" if status_val == 'error' else "🟡"
        api_display = api_name.replace('openai', 'GPT-4').replace('anthropic', 'Claude').replace('google', 'Gemini')
        st.text(f"{icon} {api_display}")
    
    if st.button("🔍 Test APIs", use_container_width=True, help="Test all API connections"):
        with st.spinner("Testing..."):
            test_results = test_all_apis()
            set_session_value('api_status', test_results)
            st.rerun()

def render_collaboration_dashboard():
    """Render enhanced agent collaboration monitoring"""
    st.markdown("## 📊 Agent Collaboration Dashboard")
    
    # Get agent status
    agent_status = get_session_value('agent_status', {})
    
    if not agent_status:
        st.info("No active collaboration sessions. Start a project to see agent activity.")
        return
    
    # Overall collaboration metrics
    total_agents = len(agent_status)
    active_agents = sum(1 for status in agent_status.values() if status.get('status') == 'working')
    completed_agents = sum(1 for status in agent_status.values() if status.get('status') == 'completed')
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Total Agents", total_agents)
    with metric_col2:
        st.metric("Active Now", active_agents)
    with metric_col3:
        st.metric("Completed", completed_agents)
    
    st.markdown("### Agent Activity Status")
    
    # Display agent activity with enhanced information
    for agent_name, status in agent_status.items():
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                agent_title = agent_name.replace('_', ' ').title()
                st.write(f"**🤖 {agent_title}**")
                if status.get('current_task'):
                    st.caption(f"Task: {status['current_task']}")
                if status.get('last_activity'):
                    st.caption(f"Last active: {status['last_activity']}")
            
            with col2:
                status_color = {
                    'idle': '🟡',
                    'working': '🟢', 
                    'completed': '✅',
                    'error': '🔴',
                    'stopped': '⏹️'
                }
                current_status = status.get('status', 'idle')
                st.write(f"{status_color.get(current_status, '⚪')} {current_status.title()}")
            
            with col3:
                progress = status.get('progress', 0)
                st.progress(progress / 100)
                st.caption(f"{progress}%")
            
            with col4:
                # Agent-specific actions
                if st.button(f"Reset", key=f"reset_{agent_name}", help=f"Reset {agent_title}"):
                    agent_status[agent_name] = {
                        "status": "idle",
                        "progress": 0,
                        "current_task": "",
                        "last_activity": None
                    }
                    set_session_value('agent_status', agent_status)
                    st.rerun()
            
            st.divider()
    
    # Model Performance Comparison
    st.markdown("### 📈 Model Performance Comparison")
    
    # Get API metrics for performance comparison
    api_metrics = get_session_value('api_metrics', {})
    
    if api_metrics:
        # Create performance comparison table
        performance_data = []
        for service, metrics in api_metrics.items():
            performance_data.append({
                'Model': service.replace('openai', 'GPT-4').replace('anthropic', 'Claude').replace('google', 'Gemini'),
                'Success Rate': f"{metrics.get('success_rate', 0)}%",
                'Avg Response Time': f"{metrics.get('avg_response_time', 0)}ms",
                'Total Requests': metrics.get('total_requests', 0)
            })
        
        if performance_data:
            import pandas as pd
            df = pd.DataFrame(performance_data)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No performance data available yet. Test APIs to see performance metrics.")
    
    # AI Consensus Sessions
    st.markdown("### 🤝 AI Consensus Sessions")
    
    chat_history = get_session_value('chat_history', [])
    consensus_messages = [msg for msg in chat_history if msg.get('agent') == 'Agent Team Consensus']
    
    if consensus_messages:
        st.metric("Consensus Sessions", len(consensus_messages))
        
        with st.expander("Recent Consensus Sessions", expanded=False):
            for i, msg in enumerate(consensus_messages[-3:], 1):  # Show last 3
                st.write(f"**Session {i}:**")
                st.write(msg.get('content', 'No content')[:200] + "...")
                st.write(f"*{msg.get('timestamp', 'No timestamp')}*")
                st.divider()
    else:
        st.info("No consensus sessions yet. Use 'Get Team Consensus' to start.")
    
    # Collaboration insights
    with st.expander("🔍 Collaboration Insights", expanded=False):
        agent_messages = [msg for msg in chat_history if msg.get('role') == 'assistant']
        
        if agent_messages:
            st.write(f"**Total Agent Responses:** {len(agent_messages)}")
            
            # Agent contribution breakdown
            agent_contributions = {}
            for msg in agent_messages:
                agent = msg.get('agent', 'Unknown')
                agent_contributions[agent] = agent_contributions.get(agent, 0) + 1
            
            if agent_contributions:
                st.write("**Agent Contributions:**")
                for agent, count in sorted(agent_contributions.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"- {agent}: {count} responses")
        else:
            st.info("No collaboration data available yet.")
    
    # Live activity feed
    st.markdown("### 📡 Live Activity Feed")
    
    # Show recent activity
    recent_activities = []
    for agent_name, status in agent_status.items():
        if status.get('status') == 'working' or status.get('current_task'):
            recent_activities.append(f"🤖 {agent_name.replace('_', ' ').title()}: {status.get('current_task', 'Processing...')}")
    
    if recent_activities:
        for activity in recent_activities[-5:]:  # Show last 5 activities
            st.text(activity)
    else:
        st.info("No recent activity to display.")

def render_system_health():
    """Render comprehensive system health monitoring"""
    st.markdown("## 🏥 System Health & Diagnostics")
    
    # Overall system status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Session health
        session_info = session_manager.get_session_info()
        error_count = session_info.get('error_count', 0)
        if error_count == 0:
            st.success("Session: Healthy")
        else:
            st.warning(f"Session: {error_count} errors")
    
    with col2:
        # Memory status
        import sys
        memory_usage = sys.getsizeof(st.session_state)
        if memory_usage < 1000000:  # 1MB
            st.success(f"Memory: {memory_usage/1000:.1f} KB")
        else:
            st.warning(f"Memory: {memory_usage/1000000:.1f} MB")
    
    with col3:
        # Agent status
        agent_status = get_session_value('agent_status', {})
        active_agents = sum(1 for status in agent_status.values() if status.get('status') == 'working')
        if active_agents > 0:
            st.info(f"Agents: {active_agents} active")
        else:
            st.success("Agents: All idle")
    
    # Model Health Status Section
    st.markdown("---")
    render_model_health_status()
    
    # Performance Metrics
    st.markdown("---")
    st.markdown("### ⚡ Performance Metrics")
    
    # Chat history metrics
    chat_history = get_session_value('chat_history', [])
    project_files = get_session_value('project_files', {})
    
    perf_col1, perf_col2, perf_col3 = st.columns(3)
    with perf_col1:
        st.metric("Chat Messages", len(chat_history))
    with perf_col2:
        st.metric("Project Files", len(project_files))
    with perf_col3:
        total_file_size = sum(len(str(content)) for content in project_files.values())
        st.metric("Total File Size", f"{total_file_size/1000:.1f} KB")
    
    # System diagnostics
    st.markdown("---")
    st.markdown("### 🔧 System Diagnostics")
    
    with st.expander("Session State Validation", expanded=False):
        validation_results = validate_session()
        for key, valid in validation_results.items():
            status = "✅" if valid else "❌"
            st.text(f"{status} {key}")
    
    with st.expander("Session Information", expanded=False):
        for key, value in session_info.items():
            st.text(f"{key}: {value}")
    
    with st.expander("Environment Variables", expanded=False):
        import os
        env_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']
        for var in env_vars:
            status = "✅" if os.getenv(var) else "❌"
            st.text(f"{status} {var}: {'Set' if os.getenv(var) else 'Not set'}")
    
    # Error logs
    st.markdown("---")
    st.markdown("### 📋 Error Logs")
    
    try:
        with open('app_errors.log', 'r') as f:
            logs = f.readlines()[-10:]  # Last 10 lines
            if logs:
                st.text_area("Recent Error Logs", '\n'.join(logs), height=200)
            else:
                st.success("No recent errors found.")
    except FileNotFoundError:
        st.info("No error log file found.")
    
    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("🔍 Test All APIs"):
            with st.spinner("Testing APIs..."):
                test_results = test_all_apis()
                set_session_value('api_status', test_results)
                st.success("API test completed!")
                st.rerun()
    
    with action_col2:
        if st.button("🧹 Clean Memory"):
            cleanup_session()
            st.success("Memory cleaned!")
            st.rerun()
    
    with action_col3:
        if st.button("🔄 Refresh Status"):
            st.success("Status refreshed!")
            st.rerun()
    
    with action_col4:
        if st.button("📊 Export Diagnostics"):
            diagnostic_data = {
                'session_info': session_info,
                'validation_results': validation_results,
                'chat_messages': len(chat_history),
                'project_files': len(project_files),
                'api_status': get_session_value('api_status', {})
            }
            
            import json
            diagnostic_json = json.dumps(diagnostic_data, indent=2, default=str)
            st.download_button(
                "📥 Download Diagnostics",
                data=diagnostic_json,
                file_name="system_diagnostics.json",
                mime="application/json"
            )

def render_settings():
    """Render application settings with enhanced safety controls"""
    from utils.session_manager import cleanup_session, partial_reset, emergency_reset, session_manager
    from utils.error_handler import log_user_action
    
    st.markdown("## ⚙️ Application Settings")
    
    # Safety Controls Section
    st.markdown("### 🛡️ Safety & Stability Controls")
    
    safety_col1, safety_col2, safety_col3 = st.columns(3)
    
    with safety_col1:
        if st.button("🧹 Clean Memory", help="Remove old data to free up memory"):
            cleanup_session()
            st.success("Memory cleanup completed!")
            log_user_action("memory_cleanup", {"source": "settings"})
            st.rerun()
    
    with safety_col2:
        if st.button("🔄 Partial Reset", help="Reset problematic state while keeping important data"):
            partial_reset()
            st.success("Partial reset completed!")
            log_user_action("partial_reset", {"source": "settings"})
            st.rerun()
    
    with safety_col3:
        if st.button("🚨 Emergency Reset", help="Complete system reset (clears everything)"):
            emergency_reset()
            st.success("Emergency reset completed!")
            log_user_action("emergency_reset", {"source": "settings"})
            st.rerun()
    
    # Agent Configuration Section
    st.markdown("### 🤖 Agent Specializations")
    st.info("Each agent is specialized for specific development tasks.")
    
    agents = get_session_value('agents', {})
    if agents:
        for agent_name, agent in agents.items():
            try:
                agent_title = agent_name.replace('_', ' ').title()
                agent_role = getattr(agent, 'role', 'Unknown Role')
                agent_spec = getattr(agent, 'specialization', 'No specialization defined')
                
                with st.expander(f"🤖 {agent_title}"):
                    st.write(f"**Role:** {agent_role}")
                    st.write(f"**Specialization:** {agent_spec}")
                    
                    # Agent health check
                    try:
                        status_info = agent.get_status_info() if hasattr(agent, 'get_status_info') else {}
                        if status_info:
                            st.json(status_info)
                    except Exception:
                        st.caption("Status information unavailable")
            except Exception as e:
                st.error(f"Error displaying {agent_name}: {str(e)}")
    else:
        st.warning("No agents loaded. Please refresh the page.")
    
    # Data Management Section  
    st.markdown("### 🗂️ Data Management")
    
    data_col1, data_col2, data_col3 = st.columns(3)
    
    with data_col1:
        chat_history = get_session_value('chat_history', [])
        if st.button(f"🧹 Clear Chat History ({len(chat_history)} msgs)"):
            set_session_value('chat_history', [])
            st.success("Chat history cleared!")
            log_user_action("chat_history_cleared", {"message_count": len(chat_history)})
            st.rerun()
    
    with data_col2:
        project_files = get_session_value('project_files', {})
        if st.button(f"🗂️ Clear Project Files ({len(project_files)} files)"):
            set_session_value('project_files', {})
            st.success("Project files cleared!")
            log_user_action("project_files_cleared", {"file_count": len(project_files)})
            st.rerun()
    
    with data_col3:
        if st.button("🔄 Reset Agent Status"):
            agent_status = get_session_value('agent_status', {})
            for agent_name in agent_status:
                agent_status[agent_name] = {
                    "status": "idle",
                    "progress": 0,
                    "current_task": "",
                    "last_activity": None
                }
            set_session_value('agent_status', agent_status)
            st.success("Agent statuses reset!")
            st.rerun()
    
    # System Information Section
    st.markdown("### 📊 System Information")
    
    try:
        session_info = session_manager.get_session_info()
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.metric("Active Agents", session_info.get('agents_loaded', 'Unknown'))
            st.metric("Chat Messages", session_info.get('chat_messages', 0))
            st.metric("Project Files", session_info.get('project_files_count', 0))
        
        with info_col2:
            st.metric("Session ID", session_info.get('session_id', 'Unknown'))
            st.metric("Error Count", session_info.get('error_count', 0))
            st.metric("Memory Loaded", "✅" if session_info.get('memory_loaded') else "❌")
        
        # Detailed session info
        with st.expander("🔍 Detailed Session Info", expanded=False):
            st.json(session_info)
            
    except Exception as e:
        st.error(f"Error getting system information: {str(e)}")
    
    # Performance Settings
    st.markdown("### ⚡ Performance Settings")
    
    perf_col1, perf_col2 = st.columns(2)
    
    with perf_col1:
        max_chat_history = st.slider(
            "Max Chat History Length", 
            min_value=50, 
            max_value=200, 
            value=100,
            help="Limit chat history to prevent memory issues"
        )
        
        if st.button("Apply Chat Limit"):
            chat_history = get_session_value('chat_history', [])
            if len(chat_history) > max_chat_history:
                set_session_value('chat_history', chat_history[-max_chat_history:])
                st.success(f"Chat history trimmed to {max_chat_history} messages")
                st.rerun()
    
    with perf_col2:
        max_project_files = st.slider(
            "Max Project Files",
            min_value=10,
            max_value=50, 
            value=20,
            help="Limit project files to prevent memory issues"
        )
        
        if st.button("Apply File Limit"):
            project_files = get_session_value('project_files', {})
            if len(project_files) > max_project_files:
                # Keep the most recent files
                sorted_files = list(project_files.items())[-max_project_files:]
                set_session_value('project_files', dict(sorted_files))
                st.success(f"Project files trimmed to {max_project_files} files")
                st.rerun()

def render_project_initiation_panel():
    """Render the main project initiation interface"""
    st.markdown("## 🚀 Project Initiation Panel")
    st.markdown("### Describe your project and watch AI agents collaborate to build it")
    
    # Project description input
    project_description = st.text_area(
        "📝 Project Description",
        placeholder="e.g., Build a task management app with team collaboration, real-time updates, user authentication, and file sharing capabilities...",
        height=120,
        help="Describe what you want to build in detail. The more specific you are, the better the AI agents can collaborate."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Project type selector
        project_type = st.selectbox(
            "🏗️ Project Type",
            options=[
                ("Web Application", ProjectType.WEB_APP),
                ("Mobile App", ProjectType.MOBILE_APP), 
                ("API Service", ProjectType.API_SERVICE),
                ("Desktop Application", ProjectType.DESKTOP_APP),
                ("Data Pipeline", ProjectType.DATA_PIPELINE),
                ("Machine Learning", ProjectType.MACHINE_LEARNING)
            ],
            format_func=lambda x: x[0]
        )
    
    with col2:
        # Complexity level slider
        complexity_mapping = {
            1: ("Simple", ProjectComplexity.SIMPLE, "Basic functionality, minimal features"),
            2: ("Medium", ProjectComplexity.MEDIUM, "Standard features, moderate complexity"),
            3: ("Complex", ProjectComplexity.COMPLEX, "Advanced features, high complexity")
        }
        
        complexity_level = st.slider(
            "⚡ Complexity Level", 
            min_value=1, 
            max_value=3, 
            value=2
        )
        
        complexity_info = complexity_mapping[complexity_level]
        st.caption(f"**{complexity_info[0]}:** {complexity_info[2]}")
    
    # Project preview
    if project_description:
        st.markdown("### 🔍 Project Preview")
        
        with st.expander("Preview Agent Assignment", expanded=True):
            complexity_obj = complexity_info[1]
            
            if complexity_obj == ProjectComplexity.SIMPLE:
                agents = ["📋 Project Manager (Planning)", "💻 Code Generator (Development)"]
                optional = ["🎨 UI Designer (Basic Interface)"]
            elif complexity_obj == ProjectComplexity.MEDIUM:
                agents = ["📋 Project Manager (Architecture)", "💻 Code Generator (Backend)", 
                         "🎨 UI Designer (Frontend)", "🧪 Test Writer (QA)"]
                optional = ["🔍 Debugger (Optimization)"]
            else:
                agents = ["📋 Project Manager (Full Planning)", "💻 Code Generator (Full Stack)", 
                         "🎨 UI Designer (Complete UX)", "🧪 Test Writer (Comprehensive Tests)", 
                         "🔍 Debugger (Performance)"]
                optional = []
            
            st.write("**Active Agents:**")
            for agent in agents:
                st.write(f"✅ {agent}")
            
            if optional:
                st.write("**Optional Agents:**")
                for agent in optional:
                    st.write(f"⚪ {agent}")
            
            estimated_time = {
                ProjectComplexity.SIMPLE: "15-30 minutes",
                ProjectComplexity.MEDIUM: "45-60 minutes", 
                ProjectComplexity.COMPLEX: "1-2 hours"
            }
            st.info(f"🕒 **Estimated Time:** {estimated_time[complexity_obj]}")
    
    # Start Orchestra button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        start_button = st.button(
            "🎼 Start Orchestra",
            disabled=not project_description.strip(),
            use_container_width=True,
            type="primary"
        )
        
        if start_button and project_description.strip():
            start_orchestration(project_description, project_type[1], complexity_info[1])

def start_orchestration(description: str, project_type: ProjectType, complexity: ProjectComplexity):
    """Initialize and start the AI agent orchestration"""
    
    with st.spinner("🎼 Initializing AI Agent Orchestra..."):
        time.sleep(2)  # Simulate initialization
        
        # Create workflow orchestrator if not exists
        if not st.session_state.workflow_orchestrator:
            st.session_state.workflow_orchestrator = WorkflowOrchestrator(st.session_state.agents)
        
        # Analyze project requirements
        project_analysis = st.session_state.workflow_orchestrator.analyze_project_requirements(
            description, project_type, complexity
        )
        
        # Create workflow steps
        workflow_steps = st.session_state.workflow_orchestrator.create_intelligent_workflow(project_analysis)
        st.session_state.workflow_orchestrator.workflow_steps = workflow_steps
        st.session_state.workflow_orchestrator.current_project = project_analysis
        
        # Set active project
        st.session_state.active_project = project_analysis
        st.session_state.workflow_status = "initializing"
        
        st.success("🎼 Orchestra initialized! Agents are ready to collaborate.")
        time.sleep(1)
        st.rerun()

def render_live_orchestration_dashboard():
    """Render the live orchestration dashboard showing real-time agent collaboration"""
    
    st.markdown("## 🎼 AI Agent Orchestra - Live Collaboration")
    
    # Project header
    project = st.session_state.active_project
    st.markdown(f"### 🏗️ {project['description'][:100]}{'...' if len(project['description']) > 100 else ''}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        project_type_str = str(project.get('project_type', 'unknown'))
        project_type_title = project_type_str.replace('_', ' ').title()
        st.metric("Project Type", project_type_title)
    with col2:
        complexity_str = str(project.get('complexity', 'unknown'))
        st.metric("Complexity", complexity_str.title()) 
    with col3:
        st.metric("Active Agents", len(project['required_agents']))
    with col4:
        if st.button("🔄 Reset Project"):
            reset_orchestration()
    
    # Get real-time status with error handling
    try:
        status = st.session_state.workflow_orchestrator.get_real_time_status()
        
        # Overall progress
        st.markdown("### 📊 Overall Progress")
        progress_value = max(0, min(100, status.get('overall_progress', 0))) / 100
        progress_bar = st.progress(progress_value)
        current_phase = status.get('current_phase', 'Initializing')
        progress_percent = status.get('overall_progress', 0)
        st.caption(f"Current Phase: **{current_phase}** | {progress_percent:.1f}% Complete")
    except Exception as e:
        st.error(f"Error getting status: {str(e)}")
        status = {
            'overall_progress': 0,
            'agent_statuses': {},
            'recent_communications': [],
            'current_phase': 'Error'
        }
    
    # Live Agent Activity Dashboard
    st.markdown("### 🤖 Live Agent Activity")
    
    # Create agent status cards with error handling
    agent_statuses = status.get('agent_statuses', {})
    if agent_statuses:
        agent_cols = st.columns(len(agent_statuses))
        
        for i, (agent_name, agent_status) in enumerate(agent_statuses.items()):
            with agent_cols[i]:
                # Agent icon mapping
                agent_icons = {
                    "project_manager": "📋",
                    "code_generator": "💻",
                    "ui_designer": "🎨", 
                    "test_writer": "🧪",
                    "debugger": "🔍"
                }
                
                icon = agent_icons.get(agent_name, "🤖")
                status_color = {
                    "idle": "🔵",
                    "analyzing": "🟡",
                    "working": "🟢",
                    "collaborating": "🟠", 
                    "completed": "✅",
                    "error": "🔴"
                }.get(agent_status['status'], "⚪")
                
                # Ensure agent_name is a string
                agent_name_str = str(agent_name) if not isinstance(agent_name, str) else agent_name
                agent_title = agent_name_str.replace('_', ' ').title()
                st.markdown(f"**{icon} {agent_title}**")
                
                # Ensure status is a string
                status_str = str(agent_status.get('status', 'idle'))
                st.caption(f"Status: {status_color} {status_str.title()}")
                
                # Progress bar for each agent with safe access
                progress_value = agent_status.get('progress', 0)
                if isinstance(progress_value, (int, float)) and progress_value > 0:
                    st.progress(min(100, max(0, progress_value)) / 100)
                    st.caption(f"{progress_value}%")
                
                # Current task with safe string handling
                current_task = agent_status.get('current_task')
                if current_task:
                    task_str = str(current_task) if not isinstance(current_task, str) else current_task
                    st.caption(f"Task: {task_str[:50]}...")
    else:
        st.info("🤖 Initializing agent status...")
    
    # Agent Collaboration Panel
    st.markdown("### 🗣️ Agent Collaboration Feed")
    
    collaboration_container = st.container()
    with collaboration_container:
        # Show recent communications
        communications = status.get('recent_communications', [])
        
        if not communications:
            st.info("🤖 Agents are preparing to collaborate...")
        else:
            for comm in communications[-5:]:  # Show last 5 messages
                try:
                    timestamp = datetime.fromisoformat(comm['timestamp']).strftime("%H:%M:%S")
                    message = comm.get('message', 'No message')
                    st.markdown(f"**{timestamp}** | {message}")
                except (ValueError, KeyError) as e:
                    st.markdown(f"• {comm.get('message', 'Communication log entry')}")
    
    # Control buttons
    st.markdown("### 🎛️ Orchestra Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Execution", disabled=st.session_state.workflow_status == "running"):
            execute_orchestration()
    
    with col2:
        if st.button("⏸️ Pause Execution", disabled=st.session_state.workflow_status != "running"):
            st.session_state.workflow_status = "paused"
            st.success("Orchestration paused")
    
    with col3:
        progress_value = status.get('overall_progress', 0)
        if st.button("📥 Download Results", disabled=progress_value < 100):
            download_project_results()

def execute_orchestration():
    """Execute the orchestration workflow"""
    st.session_state.workflow_status = "running"
    
    with st.spinner("🎼 Agents are collaborating..."):
        # Simulate workflow execution
        orchestrator = st.session_state.workflow_orchestrator
        
        # Execute steps sequentially for demo
        from core.workflow_orchestrator import AgentStatus
        
        for step in orchestrator.workflow_steps:
            if step.status == AgentStatus.IDLE:
                # Simulate execution
                step.status = AgentStatus.WORKING
                step.progress = 50
                
                # Add to communications with safe string handling
                agent_type_str = str(step.agent_type.value)
                agent_title = agent_type_str.replace('_', ' ').title()
                task_str = str(step.task)
                orchestrator.add_agent_communication(
                    f"{agent_title} started: {task_str[:50]}..."
                )
                
                time.sleep(1)  # Simulate work
                
                step.progress = 100
                step.status = AgentStatus.COMPLETED
                
                orchestrator.add_agent_communication(
                    f"{agent_title} completed task successfully!"
                )
                
                break  # Execute one step per click for demo
    
    st.success("✅ Orchestration step completed!")
    st.rerun()

def download_project_results():
    """Handle downloading of generated project files"""
    st.success("📥 Project files ready for download!")
    # Implementation for file download would go here

def reset_orchestration():
    """Reset the current orchestration"""
    st.session_state.active_project = None
    st.session_state.workflow_status = None
    if st.session_state.workflow_orchestrator:
        st.session_state.workflow_orchestrator.current_project = None
        st.session_state.workflow_orchestrator.workflow_steps = []
        st.session_state.workflow_orchestrator.agent_communications = []
        st.session_state.workflow_orchestrator.collaboration_log = []
    st.success("🔄 Project reset! Ready for new orchestration.")
    st.rerun()

def handle_orchestration_error(error_msg: str):
    """Handle orchestration errors gracefully"""
    st.error(f"Orchestration Error: {error_msg}")
    st.info("You can reset the project to start over or check the agent chat for more details.")
    if st.button("🔄 Reset Project"):
        reset_orchestration()
    
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
