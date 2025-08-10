"""
Real-time AI Model Collaboration Dashboard
Visualizes multi-agent AI workflows and model interactions
"""

import streamlit as st
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from core.model_orchestrator import orchestrator


def render_collaboration_dashboard():
    """Render the main collaboration dashboard"""
    st.markdown("## 🤝 AI Model Collaboration Dashboard")
    
    # Real-time activity monitor
    render_active_tasks()
    
    # Model performance comparison
    render_model_comparison()
    
    # Recent consensus sessions
    render_consensus_sessions()
    
    # Agent activity timeline
    render_agent_timeline()


def render_active_tasks():
    """Show currently active AI tasks"""
    st.markdown("### 🚀 Live AI Activity")
    
    active_tasks = orchestrator.get_active_tasks()
    
    if not active_tasks:
        st.info("No active AI tasks currently running.")
        return
    
    # Create columns for different models
    cols = st.columns(3)
    col_mapping = {"gpt4": 0, "claude": 1, "gemini": 2}
    model_names = {"gpt4": "GPT-4", "claude": "Claude", "gemini": "Gemini"}
    
    for task_id, task_info in active_tasks.items():
        model = task_info.get("model", "unknown")
        col_idx = col_mapping.get(model, 0)
        
        with cols[col_idx]:
            duration = time.time() - task_info["start_time"]
            
            if task_info["status"] == "processing":
                st.success(f"🔄 {model_names.get(model, model)}")
                st.caption(f"Agent: {task_info.get('agent_type', 'Unknown')}")
                st.caption(f"Duration: {duration:.1f}s")
                
                # Progress indicator
                st.progress(min(duration / 30.0, 1.0))  # Assume max 30s for visualization
                
            elif task_info["status"] == "completed":
                st.success(f"✅ {model_names.get(model, model)}")
                st.caption(f"Completed in {task_info.get('response_time', 0):.1f}s")
                
            elif task_info["status"] == "failed":
                st.error(f"❌ {model_names.get(model, model)}")
                st.caption(f"Error: {task_info.get('error', 'Unknown error')[:50]}...")


def render_model_comparison():
    """Show model performance comparison"""
    st.markdown("### 📊 Model Performance Comparison")
    
    stats = orchestrator.get_model_statistics()
    connected_models = {name: data for name, data in stats.items() if data["is_connected"]}
    
    if not connected_models:
        st.warning("No models are currently connected.")
        return
    
    # Create performance comparison table
    comparison_data = []
    for model, data in connected_models.items():
        comparison_data.append({
            "Model": model.title(),
            "Avg Response Time": f"{data['avg_response_time']}s",
            "Success Rate": f"{data['reliability']}%", 
            "Total Requests": data['success_count'],
            "Errors": data['error_count'],
            "Status": "🟢 Online" if data['is_connected'] else "🔴 Offline"
        })
    
    if comparison_data:
        st.dataframe(comparison_data, use_container_width=True)
    
    # Visual performance metrics
    col1, col2, col3 = st.columns(3)
    
    model_list = list(connected_models.keys())
    if len(model_list) >= 1:
        with col1:
            model_data = connected_models[model_list[0]]
            st.metric(
                f"{model_list[0].title()} Response Time",
                f"{model_data['avg_response_time']}s",
                delta=None
            )
    
    if len(model_list) >= 2:
        with col2:
            model_data = connected_models[model_list[1]]
            st.metric(
                f"{model_list[1].title()} Success Rate", 
                f"{model_data['reliability']}%",
                delta=None
            )
    
    if len(model_list) >= 3:
        with col3:
            model_data = connected_models[model_list[2]]
            st.metric(
                f"{model_list[2].title()} Requests",
                model_data['success_count'],
                delta=None
            )


def render_consensus_sessions():
    """Show recent consensus building sessions"""
    st.markdown("### 🗳️ AI Consensus Sessions")
    
    recent_sessions = orchestrator.get_recent_consensus_sessions(limit=3)
    
    if not recent_sessions:
        st.info("No recent consensus sessions.")
        return
    
    for session in recent_sessions:
        with st.expander(f"Consensus Session {session['id'][-8:]} - Score: {session.get('consensus_score', 0):.1f}"):
            st.write(f"**Question:** {session.get('question', 'Unknown')}")
            st.write(f"**Models Consulted:** {len(session.get('models', []))}")
            st.write(f"**Duration:** {session.get('duration', 0):.1f} seconds")
            
            # Show individual model responses
            responses = session.get('responses', {})
            if responses:
                st.write("**Model Responses:**")
                for model, response in responses.items():
                    st.write(f"- **{model.title()}:** {response[:200]}...")


def render_agent_timeline():
    """Show agent activity timeline"""
    st.markdown("### 📅 Agent Activity Timeline")
    
    # Simulate agent activity data (in a real implementation, this would come from actual logging)
    agent_specializations = {
        "PROJECT_MANAGER": {"model": "Claude", "color": "🟣", "tasks": ["Architecture planning", "Task coordination"]},
        "CODE_GENERATOR": {"model": "GPT-4", "color": "🔵", "tasks": ["Function implementation", "Algorithm design"]},
        "UI_DESIGNER": {"model": "GPT-4", "color": "🔵", "tasks": ["Component design", "Styling"]},
        "TEST_WRITER": {"model": "Gemini", "color": "🔴", "tasks": ["Test case generation", "Validation"]},
        "DEBUGGER": {"model": "Claude", "color": "🟣", "tasks": ["Bug analysis", "Code optimization"]}
    }
    
    active_tasks = orchestrator.get_active_tasks()
    
    if active_tasks:
        for task_id, task_info in active_tasks.items():
            agent_type = task_info.get("agent_type", "UNKNOWN")
            if agent_type in agent_specializations:
                agent_info = agent_specializations[agent_type]
                
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    st.write(f"{agent_info['color']} {agent_type.replace('_', ' ').title()}")
                
                with col2:
                    st.write(f"Powered by {agent_info['model']}")
                    if task_info["status"] == "processing":
                        st.progress(0.5)  # Show processing
                    elif task_info["status"] == "completed":
                        st.success("Task completed")
                
                with col3:
                    duration = time.time() - task_info["start_time"]
                    st.write(f"{duration:.1f}s")
    else:
        st.info("No recent agent activity to display.")


def render_model_voting_interface(question: str, context: str = ""):
    """Render interface for multi-model voting on decisions"""
    st.markdown("### 🗳️ AI Model Voting")
    st.write("Get consensus from multiple AI models on complex decisions:")
    
    if st.button("🚀 Start Consensus Session", key="start_consensus"):
        with st.spinner("Consulting AI models..."):
            try:
                # This would need to be adapted for async operation in Streamlit
                import asyncio
                
                # Create a simple consensus question
                full_question = f"""
                Context: {context}
                
                Question: {question}
                
                Please provide your analysis and recommendation. Focus on:
                1. Key considerations
                2. Recommended approach
                3. Potential risks or benefits
                """
                
                # Note: In a real implementation, you'd need to handle async properly
                # For now, showing the interface structure
                st.info("Consensus session initiated. Check the dashboard above for results.")
                
                # Store the session for display
                session_data = {
                    "question": full_question,
                    "timestamp": datetime.now().isoformat(),
                    "status": "processing"
                }
                
                if 'consensus_sessions' not in st.session_state:
                    st.session_state.consensus_sessions = []
                st.session_state.consensus_sessions.append(session_data)
                
            except Exception as e:
                st.error(f"Failed to start consensus session: {e}")


def render_live_collaboration_feed():
    """Show a live feed of AI model collaboration"""
    st.markdown("### 📡 Live Collaboration Feed")
    
    # Create a container for live updates
    feed_container = st.container()
    
    with feed_container:
        # Show recent AI activities
        active_tasks = orchestrator.get_active_tasks()
        
        if active_tasks:
            st.write("**Recent AI Activities:**")
            
            for task_id, task_info in list(active_tasks.items())[-5:]:  # Show last 5
                timestamp = datetime.fromtimestamp(task_info["start_time"]).strftime("%H:%M:%S")
                agent = task_info.get("agent_type", "Unknown Agent")
                model = task_info.get("model", "unknown").title()
                status = task_info.get("status", "unknown")
                
                status_icon = {"processing": "🔄", "completed": "✅", "failed": "❌"}.get(status, "⚪")
                
                st.write(f"`{timestamp}` {status_icon} **{agent}** using {model} - {status}")
        else:
            st.info("Waiting for AI activity...")
    
    # Auto-refresh option
    if st.checkbox("Auto-refresh (every 5 seconds)", key="auto_refresh_feed"):
        time.sleep(5)
        st.rerun()


def render_model_health_status():
    """Render the health status of AI models with real API testing"""
    st.markdown("### 🏥 AI Model Health Status")
    
    # Import here to avoid circular imports
    from core.api_health_checker import APIHealthChecker
    
    # Get or create health checker in session state
    if "api_health_checker" not in st.session_state:
        st.session_state.api_health_checker = APIHealthChecker()
    
    health_checker = st.session_state.api_health_checker
    
    # Add refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Test APIs", help="Test all API connections"):
            with st.spinner("Testing API connections..."):
                health_status = health_checker.run_full_health_check()
                st.session_state.api_health_status = health_status
                st.success("API tests completed!")
    
    # Get current health status
    if "api_health_status" not in st.session_state:
        st.session_state.api_health_status = health_checker.health_status
    
    health_status = st.session_state.api_health_status
    
    # Convert to display format
    models_health = {
        "GPT-4": {
            "status": "Healthy" if health_status["openai"]["status"] == "healthy" else "Error",
            "success_rate": health_status["openai"]["success_rate"],
            "response_time": "Normal" if health_status["openai"]["status"] == "healthy" else "N/A",
            "error": health_status["openai"].get("error")
        },
        "Claude": {
            "status": "Healthy" if health_status["anthropic"]["status"] == "healthy" else "Error", 
            "success_rate": health_status["anthropic"]["success_rate"],
            "response_time": "Normal" if health_status["anthropic"]["status"] == "healthy" else "N/A",
            "error": health_status["anthropic"].get("error")
        },
        "Gemini": {
            "status": "Healthy" if health_status["google"]["status"] == "healthy" else "Error",
            "success_rate": health_status["google"]["success_rate"], 
            "response_time": "Normal" if health_status["google"]["status"] == "healthy" else "N/A",
            "error": health_status["google"].get("error")
        }
    }

    # Display health status cards
    cols = st.columns(3)
    
    for i, (model_name, health_info) in enumerate(models_health.items()):
        with cols[i]:
            status = health_info["status"]
            
            if status == "Healthy":
                st.success(f"🟢 {model_name}")
                st.metric("Success Rate", f"{health_info['success_rate']}%")
                st.metric("Response Time", health_info['response_time'])
            else:
                st.error(f"🔴 {model_name}")
                st.metric("Success Rate", f"{health_info['success_rate']}%")
                if health_info.get('error'):
                    st.caption(f"Error: {health_info['error']}")
                st.caption("⚠️ Check API key in environment variables")