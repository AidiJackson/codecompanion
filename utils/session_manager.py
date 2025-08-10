"""
Advanced session state management with safety and validation
"""

import streamlit as st
import uuid
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from utils.error_handler import safe_session_state_get, safe_session_state_set, logger

class SessionManager:
    """
    Advanced session state manager with validation and safety features
    """
    
    def __init__(self):
        self.required_keys = {
            'agents': {},
            'orchestrator': None,
            'memory': None,
            'chat_history': [],
            'current_project': None,
            'agent_status': {},
            'project_files': {},
            'active_project': None,
            'workflow_status': None,
            'workflow_orchestrator': None,
            'session_id': str(uuid.uuid4())[:8],
            'initialized_at': datetime.now().isoformat(),
            'error_count': 0,
            'last_activity': datetime.now().isoformat()
        }
    
    def initialize_session(self) -> bool:
        """
        Initialize session state with all required variables
        """
        try:
            for key, default_value in self.required_keys.items():
                if not self.has_key(key):
                    safe_session_state_set(key, default_value)
            
            # Initialize agents if not already done
            if not safe_session_state_get('agents'):
                self._initialize_agents_safely()
            
            logger.info("Session initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing session: {str(e)}")
            return False
    
    def _initialize_agents_safely(self):
        """
        Safely initialize agents with error handling
        """
        try:
            from agents.project_manager import ProjectManagerAgent
            from agents.code_generator import CodeGeneratorAgent
            from agents.ui_designer import UIDesignerAgent
            from agents.test_writer import TestWriterAgent
            from agents.debugger import DebuggerAgent
            from core.orchestrator import AgentOrchestrator
            from core.workflow_orchestrator import WorkflowOrchestrator
            from core.memory import ProjectMemory
            
            # Initialize agents
            agents = {
                "project_manager": ProjectManagerAgent(),
                "code_generator": CodeGeneratorAgent(),
                "ui_designer": UIDesignerAgent(),
                "test_writer": TestWriterAgent(),
                "debugger": DebuggerAgent()
            }
            
            # Initialize memory
            memory = ProjectMemory()
            
            # Initialize orchestrators
            orchestrator = AgentOrchestrator(agents, memory)
            workflow_orchestrator = WorkflowOrchestrator(agents)
            
            # Set session state
            safe_session_state_set('agents', agents)
            safe_session_state_set('memory', memory)
            safe_session_state_set('orchestrator', orchestrator)
            safe_session_state_set('workflow_orchestrator', workflow_orchestrator)
            
            # Initialize agent status
            agent_status = {}
            for agent_name in agents:
                agent_status[agent_name] = {
                    "status": "idle",
                    "progress": 0,
                    "current_task": "",
                    "last_activity": None
                }
            safe_session_state_set('agent_status', agent_status)
            
            logger.info("Agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing agents: {str(e)}")
            # Set minimal fallback values
            safe_session_state_set('agents', {})
            safe_session_state_set('memory', None)
            safe_session_state_set('orchestrator', None)
            safe_session_state_set('workflow_orchestrator', None)
            safe_session_state_set('agent_status', {})
    
    def has_key(self, key: str) -> bool:
        """
        Check if session state has a key
        """
        try:
            return hasattr(st.session_state, key) and getattr(st.session_state, key) is not None
        except Exception:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Safely get session state value
        """
        return safe_session_state_get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Safely set session state value
        """
        try:
            result = safe_session_state_set(key, value)
            if result:
                self.update_activity()
            return result
        except Exception as e:
            logger.error(f"Error setting session key {key}: {str(e)}")
            return False
    
    def update_activity(self):
        """
        Update last activity timestamp
        """
        safe_session_state_set('last_activity', datetime.now().isoformat())
    
    def increment_error_count(self):
        """
        Increment error counter
        """
        current_count = safe_session_state_get('error_count', 0)
        safe_session_state_set('error_count', current_count + 1)
        
        # Auto-reset if too many errors
        if current_count >= 10:
            logger.warning("Too many errors, performing partial reset")
            self.partial_reset()
    
    def partial_reset(self):
        """
        Reset problematic session state while preserving important data
        """
        try:
            # Preserve important data
            chat_history = safe_session_state_get('chat_history', [])
            project_files = safe_session_state_get('project_files', {})
            
            # Clear problematic state
            keys_to_clear = ['orchestrator', 'workflow_orchestrator', 'active_project', 'workflow_status']
            for key in keys_to_clear:
                if self.has_key(key):
                    safe_session_state_set(key, self.required_keys.get(key))
            
            # Reset error count
            safe_session_state_set('error_count', 0)
            
            # Reinitialize agents
            self._initialize_agents_safely()
            
            logger.info("Partial reset completed successfully")
            
        except Exception as e:
            logger.error(f"Error during partial reset: {str(e)}")
    
    def full_reset(self):
        """
        Complete session reset
        """
        try:
            # Clear all session state
            if hasattr(st, 'session_state'):
                keys_to_clear = list(st.session_state.keys())
                for key in keys_to_clear:
                    try:
                        del st.session_state[key]
                    except Exception:
                        pass
            
            # Reinitialize
            self.initialize_session()
            
            logger.info("Full reset completed successfully")
            
        except Exception as e:
            logger.error(f"Error during full reset: {str(e)}")
    
    def validate_state(self) -> Dict[str, bool]:
        """
        Validate all session state variables
        """
        validation_results = {}
        
        for key, expected_type in self.required_keys.items():
            try:
                value = safe_session_state_get(key)
                if value is None and expected_type is not None:
                    validation_results[key] = False
                else:
                    validation_results[key] = True
            except Exception:
                validation_results[key] = False
        
        return validation_results
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get comprehensive session information
        """
        return {
            'session_id': safe_session_state_get('session_id', 'unknown'),
            'initialized_at': safe_session_state_get('initialized_at', 'unknown'),
            'last_activity': safe_session_state_get('last_activity', 'unknown'),
            'error_count': safe_session_state_get('error_count', 0),
            'chat_messages': len(safe_session_state_get('chat_history', [])),
            'project_files_count': len(safe_session_state_get('project_files', {})),
            'agents_loaded': bool(safe_session_state_get('agents')),
            'orchestrator_loaded': bool(safe_session_state_get('orchestrator')),
            'memory_loaded': bool(safe_session_state_get('memory')),
            'active_project': bool(safe_session_state_get('active_project'))
        }
    
    def cleanup_memory(self):
        """
        Clean up memory by removing old data
        """
        try:
            # Limit chat history
            chat_history = safe_session_state_get('chat_history', [])
            if len(chat_history) > 100:
                safe_session_state_set('chat_history', chat_history[-100:])
            
            # Clean up project files if too large
            project_files = safe_session_state_get('project_files', {})
            if len(project_files) > 20:
                # Keep only the 20 most recent files
                sorted_files = list(project_files.items())[-20:]
                safe_session_state_set('project_files', dict(sorted_files))
            
            logger.info("Memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during memory cleanup: {str(e)}")

# Global session manager instance
session_manager = SessionManager()

def init_session_safely() -> bool:
    """
    Initialize session state safely
    """
    return session_manager.initialize_session()

def get_session_value(key: str, default: Any = None) -> Any:
    """
    Get session state value safely
    """
    return session_manager.get(key, default)

def set_session_value(key: str, value: Any) -> bool:
    """
    Set session state value safely
    """
    return session_manager.set(key, value)

def emergency_reset():
    """
    Emergency session reset
    """
    session_manager.full_reset()

def partial_reset():
    """
    Partial session reset
    """
    session_manager.partial_reset()

def validate_session() -> Dict[str, bool]:
    """
    Validate session state
    """
    return session_manager.validate_state()

def cleanup_session():
    """
    Clean up session memory
    """
    session_manager.cleanup_memory()