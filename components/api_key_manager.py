"""
API Key Management Component for Multi-Model Integration
Secure handling of OpenAI, Anthropic, and Google API keys
"""

import os
import streamlit as st
from typing import Dict, Tuple
from core.model_orchestrator import orchestrator, reinitialize_orchestrator


def render_api_key_interface():
    """Render the API key input interface in the sidebar"""
    st.sidebar.markdown("## 🤖 AI Model Configuration")
    st.sidebar.markdown(
        "Configure your API keys to enable multi-model AI collaboration:"
    )

    # API key inputs
    api_keys = {}

    # OpenAI API Key
    st.sidebar.markdown("### 🔵 OpenAI GPT-4")
    st.sidebar.markdown(
        "*Powers: Code Generation, Creative Problem-Solving, UI Design*"
    )
    openai_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        value=os.environ.get("OPENAI_API_KEY", ""),
        help="Get your API key from https://platform.openai.com/",
        key="openai_key_input",
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        api_keys["openai"] = openai_key

    # Anthropic API Key
    st.sidebar.markdown("### 🟣 Anthropic Claude")
    st.sidebar.markdown("*Powers: Project Management, Architecture, Debugging*")
    anthropic_key = st.sidebar.text_input(
        "Anthropic API Key",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Get your API key from https://console.anthropic.com/",
        key="anthropic_key_input",
    )
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        api_keys["anthropic"] = anthropic_key

    # Google Gemini API Key
    st.sidebar.markdown("### 🔴 Google Gemini")
    st.sidebar.markdown("*Powers: Testing, Validation, Quality Assurance*")
    gemini_key = st.sidebar.text_input(
        "Google Gemini API Key",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", ""),
        help="Get your API key from https://aistudio.google.com/",
        key="gemini_key_input",
    )
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        api_keys["gemini"] = gemini_key

    # Connection status and test buttons
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Connection Status")

    if st.sidebar.button("🔄 Refresh Connections", key="refresh_connections"):
        reinitialize_orchestrator()
        st.rerun()

    # Display connection status
    status_info = get_connection_status()
    for model, info in status_info.items():
        if info["has_key"]:
            if info["is_connected"]:
                st.sidebar.success(f"✅ {model.title()} - Connected")
            else:
                st.sidebar.error(f"❌ {model.title()} - Connection Failed")
        else:
            st.sidebar.warning(f"⚠️ {model.title()} - API Key Required")

    # Test connections button
    if any(info["has_key"] for info in status_info.values()):
        if st.sidebar.button("🧪 Test All Connections", key="test_connections"):
            test_results = orchestrator.test_connections()

            for model, success in test_results.items():
                if success:
                    st.sidebar.success(f"✅ {model.title()} test successful")
                else:
                    st.sidebar.error(f"❌ {model.title()} test failed")

    # Setup instructions
    if not any(info["has_key"] for info in status_info.values()):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📋 Setup Instructions")
        st.sidebar.markdown("""
        **To get started:**
        
        1. **OpenAI**: Sign up at [platform.openai.com](https://platform.openai.com/)
        2. **Anthropic**: Sign up at [console.anthropic.com](https://console.anthropic.com/)  
        3. **Google**: Sign up at [aistudio.google.com](https://aistudio.google.com/)
        
        All services offer free trial credits to get started.
        """)

    return api_keys


def get_connection_status() -> Dict[str, Dict]:
    """Get current connection status for all models"""
    return {
        "openai": {
            "has_key": bool(os.environ.get("OPENAI_API_KEY")),
            "is_connected": orchestrator.model_status["gpt4"].is_connected,
            "model_name": "GPT-4",
            "specialization": "Code Generation, UI Design",
        },
        "anthropic": {
            "has_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "is_connected": orchestrator.model_status["claude"].is_connected,
            "model_name": "Claude",
            "specialization": "Project Management, Debugging",
        },
        "gemini": {
            "has_key": bool(os.environ.get("GEMINI_API_KEY")),
            "is_connected": orchestrator.model_status["gemini"].is_connected,
            "model_name": "Gemini",
            "specialization": "Testing, Quality Assurance",
        },
    }


def render_model_selection_interface():
    """Render model selection and preference interface"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Model Preferences")

    # Allow users to override default model assignments
    available_models = [
        name
        for name, status in orchestrator.model_status.items()
        if status.is_connected
    ]

    if available_models:
        st.sidebar.markdown("**Custom Model Assignment:**")

        model_assignments = {}
        agent_types = [
            ("Project Manager", "project_manager", "Claude (Strategic Planning)"),
            ("Code Generator", "code_generator", "GPT-4 (Creative Coding)"),
            ("UI Designer", "ui_designer", "GPT-4 (Design Creativity)"),
            ("Test Writer", "test_writer", "Gemini (Systematic Testing)"),
            ("Debugger", "debugger", "Claude (Logical Analysis)"),
        ]

        for agent_name, agent_key, default_desc in agent_types:
            selected_model = st.sidebar.selectbox(
                f"{agent_name}",
                options=available_models,
                help=f"Default: {default_desc}",
                key=f"model_select_{agent_key}",
            )
            model_assignments[agent_key] = selected_model

        return model_assignments
    else:
        st.sidebar.warning("No models connected. Please configure API keys above.")
        return {}


def render_model_performance_metrics():
    """Render real-time model performance metrics"""
    if not any(
        orchestrator.model_status[name].is_connected
        for name in orchestrator.model_status
    ):
        return

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Performance Metrics")

    stats = orchestrator.get_model_statistics()

    for model_name, model_stats in stats.items():
        if model_stats["is_connected"]:
            with st.sidebar.expander(f"📊 {model_name.title()} Stats"):
                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "Response Time", f"{model_stats['avg_response_time']:.2f}s"
                    )
                    st.metric("Success Rate", f"{model_stats['reliability']:.1f}%")

                with col2:
                    st.metric("Requests", model_stats["success_count"])
                    st.metric("Errors", model_stats["error_count"])

                if model_stats["last_used"]:
                    st.caption(f"Last used: {model_stats['last_used']}")


def check_required_keys() -> Tuple[bool, str]:
    """Check if at least one API key is configured"""
    status = get_connection_status()
    connected_models = [
        name
        for name, info in status.items()
        if info["has_key"] and info["is_connected"]
    ]

    if not connected_models:
        return False, "Please configure at least one API key to use CodeCompanion."

    if len(connected_models) == 1:
        model_name = status[connected_models[0]]["model_name"]
        return True, f"Single model mode: Using {model_name} for all tasks."

    return (
        True,
        f"Multi-model mode: {len(connected_models)} AI models available for collaboration.",
    )
