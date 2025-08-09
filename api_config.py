"""
API Configuration Module for Multi-Model Integration
"""
import os
import streamlit as st

def check_api_keys():
    """Check if API keys are available"""
    return {
        'openai': os.getenv('OPENAI_API_KEY', ''),
        'anthropic': os.getenv('ANTHROPIC_API_KEY', ''),
        'gemini': os.getenv('GEMINI_API_KEY', '')
    }

def configure_api_keys():
    """Show API key configuration interface"""
    st.header("🔑 API Key Configuration")
    st.markdown("Configure your AI model API keys to enable multi-agent collaboration:")
    
    # Get current keys
    current_keys = check_api_keys()
    
    with st.form("api_keys_form"):
        st.subheader("OpenAI (GPT-4)")
        st.markdown("**Specialization:** Code generation, creative problem-solving, UI design")
        openai_key = st.text_input(
            "OpenAI API Key", 
            value="",
            type="password",
            placeholder="sk-..."
        )
        
        st.subheader("Anthropic (Claude)")
        st.markdown("**Specialization:** Project planning, architecture decisions, debugging logic")
        anthropic_key = st.text_input(
            "Anthropic API Key", 
            value="",
            type="password",
            placeholder="sk-ant-..."
        )
        
        st.subheader("Google (Gemini)")
        st.markdown("**Specialization:** Testing strategies, validation, quality assurance")
        gemini_key = st.text_input(
            "Gemini API Key", 
            value="",
            type="password",
            placeholder="AI..."
        )
        
        submitted = st.form_submit_button("Save API Keys")
        
        if submitted:
            # Store keys in session state for this demo
            st.session_state.api_keys = {
                'OPENAI_API_KEY': openai_key,
                'ANTHROPIC_API_KEY': anthropic_key,
                'GEMINI_API_KEY': gemini_key
            }
            
            # Set environment variables for current session
            if openai_key:
                os.environ['OPENAI_API_KEY'] = openai_key
            if anthropic_key:
                os.environ['ANTHROPIC_API_KEY'] = anthropic_key
            if gemini_key:
                os.environ['GEMINI_API_KEY'] = gemini_key
                
            st.success("API keys saved! The multi-agent system is now ready.")
            st.rerun()
    
    # Show status
    st.subheader("Current Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if current_keys['openai']:
            st.success("✅ OpenAI Connected")
        else:
            st.error("❌ OpenAI Not Connected")
    
    with col2:
        if current_keys['anthropic']:
            st.success("✅ Anthropic Connected")
        else:
            st.error("❌ Anthropic Not Connected")
    
    with col3:
        if current_keys['gemini']:
            st.success("✅ Gemini Connected")
        else:
            st.error("❌ Gemini Not Connected")
    
    return any(current_keys.values())

def get_available_models():
    """Get list of available models based on API keys"""
    keys = check_api_keys()
    models = []
    
    if keys['openai']:
        models.append(('OpenAI GPT-4', 'openai', 'Code generation, UI design'))
    if keys['anthropic']:
        models.append(('Anthropic Claude', 'anthropic', 'Planning, debugging'))
    if keys['gemini']:
        models.append(('Google Gemini', 'gemini', 'Testing, QA'))
    
    return models