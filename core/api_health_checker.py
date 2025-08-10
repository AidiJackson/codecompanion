import os
import asyncio
from typing import Dict, Any, Tuple
from datetime import datetime
import streamlit as st

# AI API clients
import openai
import anthropic
from google import genai


class APIHealthChecker:
    """Real API health checking and validation for all three AI services"""
    
    def __init__(self):
        self.clients = {}
        self.health_status = {
            "openai": {"status": "unknown", "success_rate": 0, "last_test": None, "error": None},
            "anthropic": {"status": "unknown", "success_rate": 0, "last_test": None, "error": None}, 
            "google": {"status": "unknown", "success_rate": 0, "last_test": None, "error": None}
        }
    
    def initialize_clients(self):
        """Initialize all API clients with proper error handling"""
        
        # OpenAI Client
        try:
            openai_key = os.environ.get("OPENAI_API_KEY")
            if openai_key:
                self.clients["openai"] = openai.OpenAI(api_key=openai_key)
                self.health_status["openai"]["status"] = "initialized"
            else:
                self.health_status["openai"]["error"] = "API key not found in environment"
        except Exception as e:
            self.health_status["openai"]["error"] = f"Client initialization failed: {str(e)}"
        
        # Anthropic Client  
        try:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
            if anthropic_key:
                self.clients["anthropic"] = anthropic.Anthropic(api_key=anthropic_key)
                self.health_status["anthropic"]["status"] = "initialized"
            else:
                self.health_status["anthropic"]["error"] = "API key not found in environment"
        except Exception as e:
            self.health_status["anthropic"]["error"] = f"Client initialization failed: {str(e)}"
        
        # Google Gemini Client
        try:
            google_key = os.environ.get("GEMINI_API_KEY")
            if google_key:
                self.clients["google"] = genai.Client(api_key=google_key)
                self.health_status["google"]["status"] = "initialized"
            else:
                self.health_status["google"]["error"] = "API key not found in environment"
        except Exception as e:
            self.health_status["google"]["error"] = f"Client initialization failed: {str(e)}"
    
    def test_openai_connection(self) -> Tuple[bool, str]:
        """Test OpenAI API with a simple completion"""
        try:
            if "openai" not in self.clients:
                return False, "Client not initialized"
            
            response = self.clients["openai"].chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test connection. Reply with just 'OK'."}],
                max_tokens=10,
                temperature=0
            )
            
            if response.choices and response.choices[0].message.content:
                return True, "Connection successful"
            else:
                return False, "Empty response from API"
                
        except openai.AuthenticationError:
            return False, "Invalid API key"
        except openai.RateLimitError:
            return False, "Rate limit exceeded"
        except openai.APIError as e:
            return False, f"API error: {str(e)}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def test_anthropic_connection(self) -> Tuple[bool, str]:
        """Test Anthropic API with a simple message"""
        try:
            if "anthropic" not in self.clients:
                return False, "Client not initialized"
            
            response = self.clients["anthropic"].messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": "Test connection. Reply with just 'OK'."}]
            )
            
            if response.content and len(response.content) > 0:
                return True, "Connection successful"
            else:
                return False, "Empty response from API"
                
        except anthropic.AuthenticationError:
            return False, "Invalid API key"
        except anthropic.RateLimitError:
            return False, "Rate limit exceeded"
        except anthropic.APIError as e:
            return False, f"API error: {str(e)}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def test_google_connection(self) -> Tuple[bool, str]:
        """Test Google Gemini API with a simple generation"""
        try:
            if "google" not in self.clients:
                return False, "Client not initialized"
            
            response = self.clients["google"].models.generate_content(
                model="gemini-2.5-flash",
                contents="Test connection. Reply with just 'OK'."
            )
            
            if response.text:
                return True, "Connection successful"
            else:
                return False, "Empty response from API"
                
        except Exception as e:
            # Google API has various exception types
            error_msg = str(e).lower()
            if "api key" in error_msg or "authentication" in error_msg:
                return False, "Invalid API key"
            elif "quota" in error_msg or "limit" in error_msg:
                return False, "Rate limit exceeded"
            else:
                return False, f"Connection error: {str(e)}"
    
    def run_full_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check on all APIs"""
        
        self.initialize_clients()
        
        # Test OpenAI
        openai_success, openai_msg = self.test_openai_connection()
        self.health_status["openai"].update({
            "status": "healthy" if openai_success else "error",
            "success_rate": 100 if openai_success else 0,
            "last_test": datetime.now().isoformat(),
            "error": None if openai_success else openai_msg
        })
        
        # Test Anthropic
        anthropic_success, anthropic_msg = self.test_anthropic_connection()
        self.health_status["anthropic"].update({
            "status": "healthy" if anthropic_success else "error",
            "success_rate": 100 if anthropic_success else 0,
            "last_test": datetime.now().isoformat(),
            "error": None if anthropic_success else anthropic_msg
        })
        
        # Test Google
        google_success, google_msg = self.test_google_connection()
        self.health_status["google"].update({
            "status": "healthy" if google_success else "error",
            "success_rate": 100 if google_success else 0,
            "last_test": datetime.now().isoformat(),
            "error": None if google_success else google_msg
        })
        
        return self.health_status
    
    def get_working_client(self, service: str):
        """Get a working client for the specified service"""
        if service in self.clients and self.health_status[service]["status"] == "healthy":
            return self.clients[service]
        return None
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of API health status"""
        total_services = len(self.health_status)
        healthy_services = sum(1 for status in self.health_status.values() if status["status"] == "healthy")
        
        return {
            "overall_health": "healthy" if healthy_services == total_services else "degraded" if healthy_services > 0 else "critical",
            "healthy_count": healthy_services,
            "total_count": total_services,
            "services": self.health_status
        }