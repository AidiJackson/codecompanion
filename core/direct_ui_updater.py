"""
Direct UI Updater - Bypasses Event Bus Completely

This module provides direct UI updates that bypass the entire event streaming system
to prevent mock events from interfering with real API results.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st

logger = logging.getLogger(__name__)

class DirectUIUpdater:
    """
    Direct UI updater that bypasses all event streaming complexity.
    
    This class updates Streamlit session state directly without going through
    Redis, event buses, or any other middleware that might inject mock data.
    """
    
    def __init__(self):
        self.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Direct UI Updater initialized - ID: {self.execution_id}")
    
    def update_status_direct(self, message: str, agent_type: str = "system") -> None:
        """Update status directly in session state - NO event bus"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        status_entry = {
            'time': current_time,
            'message': message,
            'agent_type': agent_type,
            'execution_id': self.execution_id,
            'is_real': True,
            'source': 'DIRECT_UI_BYPASS'
        }
        
        # Initialize session state if needed
        if 'DIRECT_REAL_STATUS' not in st.session_state:
            st.session_state.DIRECT_REAL_STATUS = []
        
        st.session_state.DIRECT_REAL_STATUS.append(status_entry)
        
        logger.info(f"DIRECT UI UPDATE: {current_time} - {message} | Agent: {agent_type}")
    
    def add_agent_output_direct(self, agent: str, content: str, word_count: Optional[int] = None) -> None:
        """Add agent output directly to session state - NO event bus"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if word_count is None:
            word_count = len(content.split())
        
        output_entry = {
            'agent': agent,
            'content': content,
            'time': current_time,
            'word_count': word_count,
            'execution_id': self.execution_id,
            'is_real': True,
            'source': 'DIRECT_UI_BYPASS'
        }
        
        # Initialize session state if needed
        if 'DIRECT_REAL_OUTPUTS' not in st.session_state:
            st.session_state.DIRECT_REAL_OUTPUTS = []
        
        st.session_state.DIRECT_REAL_OUTPUTS.append(output_entry)
        
        logger.info(f"DIRECT OUTPUT: {agent} - {word_count} words at {current_time}")
    
    def add_artifact_direct(self, title: str, content: str, artifact_type: str = "analysis") -> None:
        """Add artifact directly to session state - NO event bus"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        artifact_entry = {
            'title': title,
            'content': content,
            'type': artifact_type,
            'time': current_time,
            'word_count': len(content.split()),
            'execution_id': self.execution_id,
            'is_real': True,
            'source': 'DIRECT_UI_BYPASS'
        }
        
        # Initialize session state if needed
        if 'DIRECT_REAL_ARTIFACTS' not in st.session_state:
            st.session_state.DIRECT_REAL_ARTIFACTS = []
        
        st.session_state.DIRECT_REAL_ARTIFACTS.append(artifact_entry)
        
        logger.info(f"DIRECT ARTIFACT: {title} - {len(content.split())} words")
    
    def clear_direct_data(self) -> None:
        """Clear all direct UI data"""
        direct_keys = ['DIRECT_REAL_STATUS', 'DIRECT_REAL_OUTPUTS', 'DIRECT_REAL_ARTIFACTS']
        
        for key in direct_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        logger.info("All direct UI data cleared")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of direct UI status"""
        status_count = len(st.session_state.get('DIRECT_REAL_STATUS', []))
        output_count = len(st.session_state.get('DIRECT_REAL_OUTPUTS', []))
        artifact_count = len(st.session_state.get('DIRECT_REAL_ARTIFACTS', []))
        
        return {
            'execution_id': self.execution_id,
            'status_count': status_count,
            'output_count': output_count,
            'artifact_count': artifact_count,
            'total_items': status_count + output_count + artifact_count,
            'last_update': datetime.now().strftime("%H:%M:%S")
        }


def create_direct_updater() -> DirectUIUpdater:
    """Factory function to create DirectUIUpdater"""
    return DirectUIUpdater()


def bypass_all_event_systems() -> bool:
    """
    Check if event systems should be bypassed completely.
    
    Returns True when Redis is unavailable and we should use direct UI updates.
    """
    try:
        import redis
        # Quick Redis availability check
        client = redis.from_url("redis://localhost:6379", decode_responses=True)
        client.ping()
        return False  # Redis available, don't bypass
    except:
        logger.info("Redis unavailable - bypassing all event systems")
        return True  # Redis unavailable, use direct updates