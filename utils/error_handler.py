"""
Comprehensive error handling and crash prevention utilities
"""

import logging
import time
import functools
from typing import Dict, Any, Optional, Callable
import streamlit as st
from datetime import datetime, timedelta
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class APIRateLimiter:
    """Implements exponential backoff for API calls"""
    
    def __init__(self):
        self.retry_counts = {}
        self.last_failures = {}
    
    def should_retry(self, service_name: str) -> bool:
        """Check if we should retry an API call"""
        if service_name not in self.last_failures:
            return True
            
        last_failure = self.last_failures[service_name]
        retry_count = self.retry_counts.get(service_name, 0)
        
        # Exponential backoff: 1, 2, 4, 8, 16 seconds
        wait_time = min(2 ** retry_count, 60)  # Max 60 seconds
        
        if datetime.now() - last_failure > timedelta(seconds=wait_time):
            return True
        return False
    
    def record_failure(self, service_name: str):
        """Record API failure for backoff calculation"""
        self.last_failures[service_name] = datetime.now()
        self.retry_counts[service_name] = self.retry_counts.get(service_name, 0) + 1
        logger.warning(f"API failure recorded for {service_name}, retry count: {self.retry_counts[service_name]}")
    
    def record_success(self, service_name: str):
        """Record successful API call"""
        if service_name in self.retry_counts:
            del self.retry_counts[service_name]
        if service_name in self.last_failures:
            del self.last_failures[service_name]

# Global rate limiter instance
rate_limiter = APIRateLimiter()

def safe_api_call(func: Callable, *args, timeout: int = 30, **kwargs) -> Dict[str, Any]:
    """
    Safely execute API calls with comprehensive error handling
    """
    service_name = kwargs.get('service_name', func.__name__)
    
    try:
        # Check rate limiting
        if not rate_limiter.should_retry(service_name):
            return {
                'success': False,
                'error': f'Rate limited for {service_name}. Please wait before retrying.',
                'error_type': 'rate_limit',
                'content': f'Service {service_name} is temporarily unavailable due to rate limiting.'
            }
        
        # Execute with timeout
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {timeout} seconds")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            result = func(*args, **kwargs)
            signal.alarm(0)  # Cancel the alarm
            
            # Record success
            rate_limiter.record_success(service_name)
            
            return {
                'success': True,
                'data': result,
                'content': result if isinstance(result, str) else str(result)
            }
            
        except Exception as e:
            signal.alarm(0)  # Cancel the alarm
            raise e
            
    except TimeoutError as e:
        logger.error(f"Timeout in {service_name}: {str(e)}")
        return {
            'success': False,
            'error': f'Operation timed out after {timeout} seconds',
            'error_type': 'timeout',
            'content': f'The AI service is taking too long to respond. Please try again.'
        }
        
    except Exception as e:
        rate_limiter.record_failure(service_name)
        logger.error(f"Error in {service_name}: {str(e)}\n{traceback.format_exc()}")
        
        # Specific error handling
        error_type = type(e).__name__
        if 'rate limit' in str(e).lower() or 'quota' in str(e).lower():
            error_type = 'rate_limit'
            error_msg = 'API rate limit exceeded. Please wait a moment before retrying.'
        elif 'connection' in str(e).lower() or 'network' in str(e).lower():
            error_type = 'connection'
            error_msg = 'Network connection issue. Please check your internet connection.'
        elif 'authentication' in str(e).lower() or 'api key' in str(e).lower():
            error_type = 'auth'
            error_msg = 'Authentication failed. Please check your API keys in the sidebar.'
        elif 'invalid' in str(e).lower() or 'bad request' in str(e).lower():
            error_type = 'invalid_request'
            error_msg = 'Invalid request format. Please try rephrasing your request.'
        else:
            error_type = 'unknown'
            error_msg = f'An unexpected error occurred: {str(e)}'
        
        return {
            'success': False,
            'error': error_msg,
            'error_type': error_type,
            'content': f'Error: {error_msg}'
        }

def safe_session_state_get(key: str, default: Any = None) -> Any:
    """
    Safely get session state value with comprehensive error handling
    """
    try:
        if hasattr(st, 'session_state') and hasattr(st.session_state, key):
            return getattr(st.session_state, key)
        elif hasattr(st, 'session_state') and key in st.session_state:
            return st.session_state[key]
        else:
            return default
    except Exception as e:
        logger.warning(f"Error accessing session state key '{key}': {str(e)}")
        return default

def safe_session_state_set(key: str, value: Any) -> bool:
    """
    Safely set session state value with error handling
    """
    try:
        if hasattr(st, 'session_state'):
            st.session_state[key] = value
            return True
        return False
    except Exception as e:
        logger.error(f"Error setting session state key '{key}': {str(e)}")
        return False

def validate_session_state() -> Dict[str, bool]:
    """
    Validate all required session state variables
    """
    required_keys = [
        'agents', 'orchestrator', 'memory', 'chat_history', 
        'current_project', 'agent_status', 'project_files',
        'active_project', 'workflow_status', 'workflow_orchestrator'
    ]
    
    status = {}
    for key in required_keys:
        try:
            value = safe_session_state_get(key)
            status[key] = value is not None
        except Exception:
            status[key] = False
    
    return status

def emergency_session_reset() -> None:
    """
    Emergency reset of all session state variables
    """
    try:
        if hasattr(st, 'session_state'):
            keys_to_clear = list(st.session_state.keys())
            for key in keys_to_clear:
                try:
                    del st.session_state[key]
                except Exception:
                    pass
        logger.info("Emergency session reset completed")
    except Exception as e:
        logger.error(f"Error during emergency reset: {str(e)}")

def memory_cleanup():
    """
    Clean up memory by removing old conversation history and large objects
    """
    try:
        # Limit conversation history to last 50 messages
        chat_history = safe_session_state_get('chat_history', [])
        if len(chat_history) > 50:
            st.session_state.chat_history = chat_history[-50:]
            logger.info(f"Cleaned up chat history, kept last 50 of {len(chat_history)} messages")
        
        # Clean up project files if too large
        project_files = safe_session_state_get('project_files', {})
        total_size = sum(len(str(content)) for content in project_files.values())
        if total_size > 1000000:  # 1MB limit
            # Keep only the 10 most recent files
            if len(project_files) > 10:
                sorted_files = sorted(project_files.items(), key=lambda x: len(x[1]), reverse=True)
                st.session_state.project_files = dict(sorted_files[:10])
                logger.info(f"Cleaned up project files, kept 10 of {len(project_files)} files")
        
    except Exception as e:
        logger.error(f"Error during memory cleanup: {str(e)}")

def circuit_breaker(func: Callable) -> Callable:
    """
    Decorator to implement circuit breaker pattern for API calls
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        service_name = kwargs.get('service_name', func.__name__)
        
        # Check if circuit should be open
        failure_count = rate_limiter.retry_counts.get(service_name, 0)
        if failure_count >= 5:  # Circuit opens after 5 failures
            return {
                'success': False,
                'error': f'Circuit breaker open for {service_name}. Service temporarily disabled.',
                'error_type': 'circuit_open',
                'content': f'Service {service_name} is temporarily disabled due to repeated failures. Please try again later.'
            }
        
        return func(*args, **kwargs)
    
    return wrapper

def validate_input(input_text: str, max_length: int = 10000) -> Dict[str, Any]:
    """
    Validate user input for safety and length
    """
    if not input_text or not input_text.strip():
        return {
            'valid': False,
            'error': 'Input cannot be empty',
            'sanitized': ''
        }
    
    # Remove potentially harmful content
    sanitized = input_text.strip()
    
    # Check length
    if len(sanitized) > max_length:
        return {
            'valid': False,
            'error': f'Input too long. Maximum {max_length} characters allowed.',
            'sanitized': sanitized[:max_length]
        }
    
    # Basic security checks
    suspicious_patterns = ['<script', 'javascript:', 'eval(', 'exec(']
    if any(pattern in sanitized.lower() for pattern in suspicious_patterns):
        return {
            'valid': False,
            'error': 'Input contains potentially unsafe content',
            'sanitized': sanitized
        }
    
    return {
        'valid': True,
        'error': None,
        'sanitized': sanitized
    }

def log_user_action(action: str, details: Dict[str, Any] = None):
    """
    Log user actions for debugging and monitoring
    """
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details or {},
            'session_id': safe_session_state_get('session_id', 'unknown')
        }
        logger.info(f"User action: {action} - {details}")
    except Exception as e:
        logger.error(f"Error logging user action: {str(e)}")

def get_error_help_message(error_type: str) -> str:
    """
    Get helpful error messages for users
    """
    error_messages = {
        'rate_limit': 'The AI service is currently busy. Please wait a moment and try again.',
        'timeout': 'The request is taking too long. Please try a simpler request or try again later.',
        'connection': 'Cannot connect to AI services. Please check your internet connection.',
        'auth': 'API authentication failed. Please check your API keys in the sidebar settings.',
        'invalid_request': 'The request format is invalid. Please try rephrasing your request.',
        'circuit_open': 'This service is temporarily disabled due to repeated errors. Please try again in a few minutes.',
        'memory_limit': 'The conversation is too long. Please use the "Clear Chat History" button and start fresh.',
        'unknown': 'An unexpected error occurred. Please try refreshing the page or contact support.'
    }
    
    return error_messages.get(error_type, error_messages['unknown'])