"""
Simple Multi-Model API Configuration App
"""
import streamlit as st
import os
from api_config import configure_api_keys, check_api_keys, get_available_models

# Page configuration
st.set_page_config(
    page_title="CodeCompanion - Multi-Agent AI Development",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🤖 CodeCompanion - Multi-Agent AI Development System")
    st.markdown("### Multi-Model Integration with Claude, GPT-4, and Gemini")
    
    # Check if API keys are configured
    current_keys = check_api_keys()
    keys_configured = any(current_keys.values())
    
    if not keys_configured:
        st.info("👇 Please configure your API keys to get started with the multi-agent system")
        configure_api_keys()
    else:
        # Show main interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("Multi-Agent Collaboration")
            
            # Show available models
            available_models = get_available_models()
            st.subheader("Available AI Models")
            
            for model_name, model_type, specialization in available_models:
                with st.expander(f"{model_name} - {specialization}"):
                    st.markdown(f"**Type:** {model_type}")
                    st.markdown(f"**Specialization:** {specialization}")
                    if model_type == 'openai':
                        st.markdown("**Role:** Code Generator & UI Designer Agent")
                    elif model_type == 'anthropic':
                        st.markdown("**Role:** Project Manager & Debugger Agent")
                    elif model_type == 'gemini':
                        st.markdown("**Role:** Test Writer & Quality Assurance Agent")
            
            # Demo section
            st.subheader("🚀 Try Multi-Model Collaboration")
            if st.button("Start Demo Project"):
                st.success("Multi-agent collaboration demo starting...")
                
                # Show model assignments
                st.markdown("### Model Assignments:")
                for model_name, model_type, _ in available_models:
                    if model_type == 'anthropic':
                        st.info(f"🧠 {model_name} → Project planning and architecture")
                    elif model_type == 'openai':
                        st.info(f"⚡ {model_name} → Code generation and UI design")
                    elif model_type == 'gemini':
                        st.info(f"🔍 {model_name} → Testing and quality assurance")
        
        with col2:
            st.header("Configuration")
            
            # Quick reconfigure option
            if st.button("Reconfigure API Keys"):
                st.session_state.show_config = True
                st.rerun()
            
            if st.session_state.get('show_config', False):
                configure_api_keys()
                if st.button("Hide Configuration"):
                    st.session_state.show_config = False
                    st.rerun()
            
            # Model status
            st.subheader("Model Status")
            for key, value in current_keys.items():
                if value:
                    st.success(f"✅ {key.upper()}")
                else:
                    st.error(f"❌ {key.upper()}")

if __name__ == "__main__":
    main()