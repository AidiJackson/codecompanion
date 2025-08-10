"""
Isolated Real API Execution Engine
Completely bypasses all simulation systems and orchestration complexity.
Makes direct, authenticated API calls and displays results immediately.
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import streamlit as st
from core.direct_ui_updater import DirectUIUpdater

logger = logging.getLogger(__name__)

class IsolatedRealExecutor:
    """
    Isolated real execution engine that completely bypasses simulation systems.
    Makes direct API calls and updates UI immediately with real results.
    """
    
    def __init__(self):
        """Initialize with API clients and direct UI updater"""
        self.execution_id = f"isolated_{datetime.now().strftime('%H%M%S')}"
        self.ui_updater = DirectUIUpdater()
        logger.info(f"🔧 IsolatedRealExecutor initialized: {self.execution_id}")
        self.ui_updater.update_status_direct("Isolated Real Executor initialized", "system")
    
    def check_api_keys(self) -> Dict[str, bool]:
        """Check which API keys are available using strict settings"""
        from settings import settings
        
        keys = settings.get_available_models()
        # Convert to expected format
        available_keys = {
            'Claude': keys['claude'],
            'GPT-4': keys['gpt-4'],
            'Gemini': keys['gemini']
        }
        logger.info(f"🔑 API keys available: {available_keys}")
        return available_keys
    
    def add_real_status(self, message: str):
        """Add real status using direct UI updater - bypasses all event systems"""
        self.ui_updater.update_status_direct(message, "isolated_executor")
        logger.info(f"📢 DIRECT UI STATUS: {message}")
        
        # Also maintain backward compatibility
        current_time = datetime.now().strftime("%H:%M:%S")
        if 'ISOLATED_REAL_STATUS' not in st.session_state:
            st.session_state.ISOLATED_REAL_STATUS = []
        
        st.session_state.ISOLATED_REAL_STATUS.append({
            'time': current_time,
            'message': message,
            'timestamp_obj': datetime.now(),
            'source': 'ISOLATED_REAL_EXECUTOR',
            'execution_id': self.execution_id
        })
    
    def add_real_output(self, agent_name: str, content: str):
        """Add real agent output using direct UI updater"""
        word_count = len(content.split())
        self.ui_updater.add_agent_output_direct(agent_name, content, word_count)
        logger.info(f"🤖 DIRECT UI OUTPUT: {agent_name} - {len(content)} chars")
        
        # Also maintain backward compatibility
        current_time = datetime.now().strftime("%H:%M:%S")
        if 'ISOLATED_REAL_OUTPUTS' not in st.session_state:
            st.session_state.ISOLATED_REAL_OUTPUTS = []
        
        st.session_state.ISOLATED_REAL_OUTPUTS.append({
            'agent': agent_name,
            'content': content,
            'time': current_time,
            'timestamp_obj': datetime.now(),
            'word_count': word_count,
            'source': 'ISOLATED_REAL_EXECUTOR',
            'execution_id': self.execution_id
        })
        
        logger.info(f"✅ Added isolated output - Total: {len(st.session_state.ISOLATED_REAL_OUTPUTS)}")
    
    def execute_real_claude_only(self, project_description: str) -> Dict[str, Any]:
        """Execute ONLY real Claude API call - completely isolated"""
        start_time = datetime.now()
        current_time = start_time.strftime("%H:%M:%S")
        
        logger.info(f"🚀 ISOLATED EXECUTION STARTED: {current_time}")
        
        self.add_real_status(f"🔥 ISOLATED Real Claude execution started at {current_time}")
        
        try:
            # Import and use Claude directly with strict settings
            import anthropic
            from settings import settings
            
            if not settings.ANTHROPIC_API_KEY:
                error_msg = "❌ ANTHROPIC_API_KEY not found in strict configuration"
                self.add_real_status(error_msg)
                return {"status": "failed", "error": "Missing API key"}
            
            api_key = settings.ANTHROPIC_API_KEY
            
            self.add_real_status("🔑 API key found, creating Claude client...")
            
            # Create client
            client = anthropic.Anthropic(api_key=api_key)
            
            self.add_real_status("🤖 Claude client created, making API call...")
            
            # Make REAL API call
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"""REAL API CALL - Project Analysis Request:

Project Description: {project_description}

Please provide a comprehensive project analysis including:
1. Technical requirements
2. Architecture recommendations  
3. Implementation approach
4. Key components needed

This is a REAL API call - please provide authentic, detailed analysis."""
                }]
            )
            
            # Extract result with proper error handling
            if response.content and len(response.content) > 0:
                # Handle different content block types
                content_block = response.content[0]
                if hasattr(content_block, 'text'):
                    result_content = content_block.text
                else:
                    result_content = str(content_block)
            else:
                result_content = "No content received from Claude API"
            
            completion_time = datetime.now().strftime("%H:%M:%S")
            
            logger.info(f"✅ REAL Claude API call completed: {len(result_content)} chars")
            
            self.add_real_status(f"✅ REAL Claude API call completed at {completion_time}")
            self.add_real_output("Claude (Real API)", result_content)
            
            return {
                "status": "completed",
                "execution_id": self.execution_id,
                "start_time": start_time.strftime("%H:%M:%S"),
                "completion_time": completion_time,
                "result": result_content,
                "word_count": len(result_content.split()),
                "source": "ISOLATED_REAL_EXECUTOR"
            }
            
        except Exception as e:
            error_time = datetime.now().strftime("%H:%M:%S")
            error_msg = f"❌ REAL Claude API error at {error_time}: {str(e)}"
            logger.error(error_msg)
            
            self.add_real_status(error_msg)
            
            return {
                "status": "failed",
                "error": str(e),
                "execution_id": self.execution_id,
                "error_time": error_time
            }
    
    def display_isolated_results(self):
        """Display ONLY isolated real results - NO simulation data"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        st.markdown("### 🔥 ISOLATED REAL EXECUTION RESULTS")
        st.info(f"⏰ Current Real Time: {current_time}")
        st.info(f"🆔 Execution ID: {self.execution_id}")
        
        # Show isolated status updates
        if 'ISOLATED_REAL_STATUS' in st.session_state and st.session_state.ISOLATED_REAL_STATUS:
            st.markdown("#### 📊 ISOLATED Status Updates")
            for status in st.session_state.ISOLATED_REAL_STATUS:
                st.write(f"⏰ {status['time']} - {status['message']} | ISOLATED REAL")
        else:
            st.warning("❌ No isolated status updates found")
        
        # Show isolated outputs
        if 'ISOLATED_REAL_OUTPUTS' in st.session_state and st.session_state.ISOLATED_REAL_OUTPUTS:
            st.markdown("#### 🤖 ISOLATED Agent Outputs")
            for output in st.session_state.ISOLATED_REAL_OUTPUTS:
                with st.expander(f"📄 {output['agent']} - {output['time']} | ISOLATED REAL", expanded=True):
                    st.markdown(output['content'])
                    st.caption(f"Word count: {output['word_count']} | Generated via ISOLATED real API call")
        else:
            st.warning("❌ No isolated outputs found")