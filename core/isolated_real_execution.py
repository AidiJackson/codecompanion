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

logger = logging.getLogger(__name__)

class IsolatedRealExecutor:
    """
    Isolated real execution engine that completely bypasses simulation systems.
    Makes direct API calls and updates UI immediately with real results.
    """
    
    def __init__(self):
        """Initialize with API clients"""
        self.execution_id = f"isolated_{datetime.now().strftime('%H%M%S')}"
        logger.info(f"🔧 IsolatedRealExecutor initialized: {self.execution_id}")
    
    def check_api_keys(self) -> Dict[str, bool]:
        """Check which API keys are available"""
        keys = {
            'Claude': bool(os.environ.get('ANTHROPIC_API_KEY')),
            'GPT-4': bool(os.environ.get('OPENAI_API_KEY')),
            'Gemini': bool(os.environ.get('GEMINI_API_KEY'))
        }
        logger.info(f"🔑 API keys available: {keys}")
        return keys
    
    def add_real_status(self, message: str):
        """Add real status with current timestamp - NO simulation interference"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        logger.info(f"📢 ISOLATED STATUS: {current_time} - {message}")
        
        # Ensure session state exists
        if 'ISOLATED_REAL_STATUS' not in st.session_state:
            st.session_state.ISOLATED_REAL_STATUS = []
        
        # Add ONLY real event
        st.session_state.ISOLATED_REAL_STATUS.append({
            'time': current_time,
            'message': message,
            'timestamp_obj': datetime.now(),
            'source': 'ISOLATED_REAL_EXECUTOR',
            'execution_id': self.execution_id
        })
        
        # Force UI update
        st.rerun()
    
    def add_real_output(self, agent_name: str, content: str):
        """Add real agent output - NO simulation interference"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        logger.info(f"🤖 ISOLATED OUTPUT: {agent_name} - {len(content)} chars")
        
        # Ensure session state exists
        if 'ISOLATED_REAL_OUTPUTS' not in st.session_state:
            st.session_state.ISOLATED_REAL_OUTPUTS = []
        
        # Add ONLY real output
        st.session_state.ISOLATED_REAL_OUTPUTS.append({
            'agent': agent_name,
            'content': content,
            'time': current_time,
            'timestamp_obj': datetime.now(),
            'word_count': len(content.split()),
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
            # Import and use Claude directly
            import anthropic
            
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                error_msg = "❌ ANTHROPIC_API_KEY not found"
                self.add_real_status(error_msg)
                return {"status": "failed", "error": "Missing API key"}
            
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
            
            # Extract result
            result_content = response.content[0].text
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