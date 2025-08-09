from typing import Dict, List, Any, Optional
import json
import re
from .base_agent import BaseAgent

class DebuggerAgent(BaseAgent):
    """Debugger Agent - Specialized in code analysis, bug fixing, and optimization"""
    
    def __init__(self):
        super().__init__(
            name="Debugger",
            role="Software Debugger",
            specialization="Code analysis, bug detection, debugging, performance optimization, and code quality improvement"
        )
        self.common_patterns = {
            "syntax_errors": [
                r"SyntaxError",
                r"IndentationError",
                r"unexpected token",
                r"missing \)",
                r"missing \}",
                r"unclosed"
            ],
            "runtime_errors": [
                r"AttributeError",
                r"TypeError",
                r"ValueError",
                r"KeyError",
                r"IndexError",
                r"NullPointerException",
                r"undefined"
            ],
            "security_issues": [
                r"eval\(",
                r"exec\(",
                r"os\.system",
                r"subprocess\.call",
                r"SQL injection",
                r"XSS"
            ],
            "performance_issues": [
                r"O\(n\^2\)",
                r"nested loop",
                r"memory leak",
                r"inefficient query"
            ]
        }
    
    def process_request(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process debugging and optimization requests"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Debug request: {request}\n\nCode context: {json.dumps(context, indent=2)}"}
        ]
        
        response_content = self.call_llm(messages)
        
        # Analyze code and generate fixes
        analysis_results = self.analyze_code(request, context)
        fixed_files = self.generate_fixes(request, context, analysis_results)
        
        # Add analysis to response
        if analysis_results:
            response_content += f"\n\n🔍 **Code Analysis Results:**\n{self.format_analysis(analysis_results)}"
        
        # Determine handoffs
        handoff_to = None
        if any(keyword in request.lower() for keyword in ["test", "testing", "validate"]):
            handoff_to = "test_writer"
        elif any(keyword in request.lower() for keyword in ["implement", "generate", "create"]):
            handoff_to = "code_generator"
        elif any(keyword in request.lower() for keyword in ["ui", "interface", "frontend"]):
            handoff_to = "ui_designer"
        
        self.add_to_history(request, response_content)
        
        return {
            "content": response_content,
            "handoff_to": handoff_to,
            "agent": self.name,
            "files": fixed_files,
            "analysis": analysis_results
        }
    
    def process_handoff(self, handoff_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process handoff from another agent"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Code review handoff: {handoff_content}\n\nDebugging context: {json.dumps(context, indent=2)}"}
        ]
        
        response_content = self.call_llm(messages, temperature=0.3)  # Lower temperature for debugging
        
        # Analyze the handed-off content
        analysis_results = self.analyze_code(handoff_content, context)
        fixed_files = self.generate_fixes(handoff_content, context, analysis_results)
        
        if analysis_results:
            response_content += f"\n\n🔍 **Debug Analysis:**\n{self.format_analysis(analysis_results)}"
        
        self.add_to_history(f"Handoff: {handoff_content}", response_content)
        
        return {
            "content": f"**Debugger Analysis:**\n\n{response_content}",
            "agent": self.name,
            "files": fixed_files,
            "analysis": analysis_results
        }
    
    def analyze_code(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code for potential issues"""
        analysis = {
            "syntax_issues": [],
            "runtime_issues": [],
            "security_issues": [],
            "performance_issues": [],
            "code_quality": [],
            "suggestions": []
        }
        
        # Get project files from context if available
        project_files = context.get("project_files", {})
        
        # Analyze content and project files
        all_content = content + "\n" + "\n".join(project_files.values()) if project_files else content
        
        # Check for common issues
        for category, patterns in self.common_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, all_content, re.IGNORECASE)
                if matches:
                    analysis[category].append({
                        "pattern": pattern,
                        "matches": len(matches),
                        "severity": self.get_severity(category, pattern)
                    })
        
        # Code quality checks
        analysis["code_quality"] = self.check_code_quality(all_content)
        
        # Generate suggestions
        analysis["suggestions"] = self.generate_suggestions(analysis)
        
        return analysis
    
    def get_severity(self, category: str, pattern: str) -> str:
        """Determine severity of an issue"""
        high_severity = ["eval(", "exec(", "os.system", "SQL injection", "XSS"]
        medium_severity = ["AttributeError", "TypeError", "memory leak"]
        
        if any(hs in pattern for hs in high_severity):
            return "HIGH"
        elif any(ms in pattern for ms in medium_severity):
            return "MEDIUM"
        else:
            return "LOW"
    
    def check_code_quality(self, content: str) -> List[Dict[str, Any]]:
        """Check code quality issues"""
        quality_issues = []
        
        # Check for long functions (simple heuristic)
        function_pattern = r'def\s+\w+.*?(?=\ndef|\Z)'
        functions = re.findall(function_pattern, content, re.DOTALL | re.MULTILINE)
        
        for func in functions:
            lines = func.split('\n')
            if len(lines) > 50:  # Arbitrary threshold
                quality_issues.append({
                    "issue": "Long function",
                    "description": f"Function has {len(lines)} lines, consider breaking it down",
                    "severity": "MEDIUM"
                })
        
        # Check for missing docstrings
        if 'def ' in content and '"""' not in content and "'''" not in content:
            quality_issues.append({
                "issue": "Missing docstrings",
                "description": "Functions should have docstrings for better documentation",
                "severity": "LOW"
            })
        
        # Check for magic numbers
        magic_number_pattern = r'\b(?<!=\s)\d{2,}\b(?!\s*[;,\]\)])'
        magic_numbers = re.findall(magic_number_pattern, content)
        if magic_numbers:
            quality_issues.append({
                "issue": "Magic numbers",
                "description": f"Found {len(magic_numbers)} magic numbers, consider using named constants",
                "severity": "LOW"
            })
        
        return quality_issues
    
    def generate_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []
        
        # Security suggestions
        if analysis["security_issues"]:
            suggestions.append("🔒 Review security issues and implement input validation")
            suggestions.append("🔐 Consider using parameterized queries to prevent SQL injection")
            suggestions.append("🛡️ Implement proper authentication and authorization")
        
        # Performance suggestions
        if analysis["performance_issues"]:
            suggestions.append("⚡ Optimize algorithms and data structures for better performance")
            suggestions.append("📊 Consider caching frequently accessed data")
            suggestions.append("🔄 Review database queries for optimization opportunities")
        
        # Code quality suggestions
        if analysis["code_quality"]:
            suggestions.append("✨ Improve code documentation and add docstrings")
            suggestions.append("🧹 Refactor long functions into smaller, focused units")
            suggestions.append("📏 Use named constants instead of magic numbers")
        
        # General suggestions
        suggestions.extend([
            "🧪 Add comprehensive unit tests for better code reliability",
            "📝 Implement proper error handling and logging",
            "🔍 Consider using static analysis tools for continuous code quality",
            "🚀 Implement CI/CD pipeline for automated testing and deployment"
        ])
        
        return suggestions
    
    def format_analysis(self, analysis: Dict[str, Any]) -> str:
        """Format analysis results for display"""
        formatted = ""
        
        # Summary
        total_issues = sum(len(issues) for key, issues in analysis.items() 
                          if key in ["syntax_issues", "runtime_issues", "security_issues", "performance_issues"])
        
        formatted += f"**Summary:** {total_issues} potential issues found\n\n"
        
        # Issue categories
        categories = {
            "security_issues": "🔒 Security Issues",
            "performance_issues": "⚡ Performance Issues",
            "runtime_issues": "🐛 Runtime Issues", 
            "syntax_issues": "📝 Syntax Issues"
        }
        
        for key, title in categories.items():
            issues = analysis.get(key, [])
            if issues:
                formatted += f"**{title}:**\n"
                for issue in issues:
                    severity = issue.get('severity', 'LOW')
                    pattern = issue.get('pattern', '')
                    matches = issue.get('matches', 0)
                    formatted += f"- {severity}: {pattern} ({matches} occurrences)\n"
                formatted += "\n"
        
        # Code quality
        quality_issues = analysis.get("code_quality", [])
        if quality_issues:
            formatted += "**📊 Code Quality:**\n"
            for issue in quality_issues:
                formatted += f"- {issue['severity']}: {issue['issue']} - {issue['description']}\n"
            formatted += "\n"
        
        # Suggestions
        suggestions = analysis.get("suggestions", [])
        if suggestions:
            formatted += "**💡 Suggestions:**\n"
            for suggestion in suggestions[:5]:  # Limit to top 5
                formatted += f"- {suggestion}\n"
        
        return formatted
    
    def generate_fixes(self, request: str, context: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate fixed code files"""
        files = {}
        
        # Get project files from context
        project_files = context.get("project_files", {})
        
        if not project_files:
            # Generate generic debugging utilities if no specific files to fix
            files.update(self.generate_debugging_utilities())
            return files
        
        # Fix issues in existing files
        for filename, content in project_files.items():
            fixed_content = self.fix_code_issues(content, analysis)
            if fixed_content != content:
                files[f"fixed_{filename}"] = fixed_content
        
        # Add debugging utilities
        files.update(self.generate_debugging_utilities())
        
        return files
    
    def fix_code_issues(self, code: str, analysis: Dict[str, Any]) -> str:
        """Apply automatic fixes to code where possible"""
        fixed_code = code
        
        # Fix common Python issues
        if "python" in code or "def " in code:
            # Add error handling for common patterns
            if "open(" in fixed_code and "with " not in fixed_code:
                fixed_code = self.add_context_managers(fixed_code)
            
            # Add try-catch blocks for risky operations
            if any(pattern in fixed_code for pattern in ["requests.get", "json.loads", "int("]):
                fixed_code = self.add_error_handling(fixed_code)
            
            # Add input validation
            if "input(" in fixed_code:
                fixed_code = self.add_input_validation(fixed_code)
        
        # Fix JavaScript issues
        if "javascript" in code.lower() or "function " in code:
            # Add null checks
            fixed_code = self.add_null_checks(fixed_code)
            
            # Fix async/await patterns
            fixed_code = self.fix_async_patterns(fixed_code)
        
        return fixed_code
    
    def add_context_managers(self, code: str) -> str:
        """Add context managers for file operations"""
        # Simple pattern replacement for file operations
        pattern = r'(\w+)\s*=\s*open\((.*?)\)'
        replacement = r'with open(\2) as \1:'
        return re.sub(pattern, replacement, code)
    
    def add_error_handling(self, code: str) -> str:
        """Add basic error handling"""
        if "try:" not in code:
            # Wrap risky operations in try-catch
            risky_patterns = ["requests.get", "json.loads", "int(", "float("]
            for pattern in risky_patterns:
                if pattern in code and "try:" not in code:
                    lines = code.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and not line.strip().startswith('#'):
                            # Add try-except around this line
                            indent = len(line) - len(line.lstrip())
                            spaces = ' ' * indent
                            lines[i] = f"{spaces}try:\n{line}\n{spaces}except Exception as e:\n{spaces}    logger.error(f'Error: {{e}}')\n{spaces}    raise"
                            break
                    code = '\n'.join(lines)
        return code
    
    def add_input_validation(self, code: str) -> str:
        """Add input validation"""
        # Add validation for user inputs
        if "input(" in code:
            code = code.replace(
                "input(",
                "validate_input(input("
            )
            
            # Add validation function if not present
            if "def validate_input" not in code:
                validation_func = '''
def validate_input(user_input):
    """Validate user input for security"""
    if not user_input or not isinstance(user_input, str):
        raise ValueError("Invalid input")
    # Add more validation as needed
    return user_input.strip()
'''
                code = validation_func + "\n" + code
        
        return code
    
    def add_null_checks(self, code: str) -> str:
        """Add null checks for JavaScript"""
        # Simple null check additions
        if "." in code:
            # Add optional chaining where appropriate
            code = re.sub(r'(\w+)\.(\w+)', r'\1?.\2', code)
        return code
    
    def fix_async_patterns(self, code: str) -> str:
        """Fix async/await patterns"""
        # Ensure async functions use await properly
        if "async function" in code and "await" not in code:
            # Add await to Promise-returning calls
            promise_patterns = ["fetch(", "axios.", "request("]
            for pattern in promise_patterns:
                code = code.replace(pattern, f"await {pattern}")
        return code
    
    def generate_debugging_utilities(self) -> Dict[str, str]:
        """Generate debugging utility files"""
        files = {}
        
        files["debug_utils.py"] = '''"""
Debugging and monitoring utilities
"""
import logging
import traceback
import time
import functools
from typing import Any, Callable, Dict, List
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DebugMonitor:
    """Debug monitoring and profiling utilities"""
    
    def __init__(self):
        self.call_counts = {}
        self.execution_times = {}
        self.errors = []
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile function execution"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            # Track call count
            self.call_counts[func_name] = self.call_counts.get(func_name, 0) + 1
            
            # Track execution time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                self.errors.append({
                    'function': func_name,
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'timestamp': datetime.now().isoformat()
                })
                logger.error(f"Error in {func_name}: {e}")
                raise
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                if func_name not in self.execution_times:
                    self.execution_times[func_name] = []
                self.execution_times[func_name].append(execution_time)
                
                logger.debug(f"{func_name} executed in {execution_time:.4f}s")
        
        return wrapper
    
    def log_function_calls(self, func: Callable) -> Callable:
        """Decorator to log function calls"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.info(f"Calling {func_name} with args: {args}, kwargs: {kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"{func_name} returned: {type(result).__name__}")
                return result
            except Exception as e:
                logger.error(f"{func_name} raised {type(e).__name__}: {e}")
                raise
        
        return wrapper
    
    def get_stats(self) -> Dict[str, Any]:
        """Get debugging statistics"""
        stats = {
            'call_counts': self.call_counts,
            'average_execution_times': {},
            'total_errors': len(self.errors),
            'recent_errors': self.errors[-5:] if self.errors else []
        }
        
        # Calculate average execution times
        for func_name, times in self.execution_times.items():
            if times:
                stats['average_execution_times'][func_name] = {
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'total_calls': len(times)
                }
        
        return stats
    
    def save_debug_report(self, filename: str = None):
        """Save debug report to file"""
        if not filename:
            filename = f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.get_stats(),
            'system_info': {
                'python_version': os.sys.version,
                'working_directory': os.getcwd()
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Debug report saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save debug report: {e}")

# Global debug monitor instance
debug_monitor = DebugMonitor()

def debug_trace(func: Callable) -> Callable:
    """Decorator to trace function execution"""
    return debug_monitor.log_function_calls(func)

def profile(func: Callable) -> Callable:
    """Decorator to profile function performance"""
    return debug_monitor.profile_function(func)

def validate_input(value: Any, expected_type: type = None, min_length: int = None, max_length: int = None) -> Any:
    """Validate input values"""
    if value is None:
        raise ValueError("Input cannot be None")
    
    if expected_type and not isinstance(value, expected_type):
        raise TypeError(f"Expected {expected_type.__name__}, got {type(value).__name__}")
    
    if isinstance(value, str):
        if min_length and len(value) < min_length:
            raise ValueError(f"Input too short, minimum length: {min_length}")
        if max_length and len(value) > max_length:
            raise ValueError(f"Input too long, maximum length: {max_length}")
    
    return value

def safe_execute(func: Callable, *args, default=None, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Safe execute failed: {e}")
        return default

def memory_usage():
    """Get current memory usage"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'percent': process.memory_percent()
        }
    except ImportError:
        return {"error": "psutil not available"}

def check_system_resources():
    """Check system resource usage"""
    try:
        import psutil
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
    except ImportError:
        return {"error": "psutil not available"}

class CodeAnalyzer:
    """Static code analysis utilities"""
    
    @staticmethod
    def find_security_issues(code: str) -> List[Dict[str, str]]:
        """Find potential security issues in code"""
        issues = []
        
        # Check for dangerous functions
        dangerous_patterns = [
            (r'eval\(', 'Use of eval() can be dangerous'),
            (r'exec\(', 'Use of exec() can be dangerous'),
            (r'os\.system\(', 'Use of os.system() can be dangerous'),
            (r'subprocess\.call\([^)]*shell=True', 'Shell injection risk'),
            (r'input\([^)]*\)', 'Unvalidated user input')
        ]
        
        for pattern, message in dangerous_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                issues.append({
                    'type': 'security',
                    'message': message,
                    'line': code[:match.start()].count('\n') + 1
                })
        
        return issues
    
    @staticmethod
    def find_performance_issues(code: str) -> List[Dict[str, str]]:
        """Find potential performance issues"""
        issues = []
        
        # Check for performance anti-patterns
        performance_patterns = [
            (r'for\s+\w+\s+in\s+range\(len\(', 'Use enumerate() instead of range(len())'),
            (r'\+\=.*\n.*for', 'String concatenation in loop can be slow'),
            (r'\.append\([^)]*\)\s*\n.*for.*in.*range', 'List comprehension might be faster')
        ]
        
        for pattern, message in performance_patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                issues.append({
                    'type': 'performance',
                    'message': message,
                    'line': code[:match.start()].count('\n') + 1
                })
        
        return issues

# Example usage functions
def test_debug_utilities():
    """Test the debugging utilities"""
    
    @debug_trace
    @profile
    def example_function(x: int, y: int) -> int:
        """Example function for testing"""
        time.sleep(0.1)  # Simulate some work
        return x + y
    
    @debug_trace
    def example_error_function():
        """Function that raises an error"""
        raise ValueError("This is a test error")
    
    # Test successful function
    result = example_function(5, 10)
    print(f"Result: {result}")
    
    # Test error handling
    try:
        example_error_function()
    except ValueError:
        pass
    
    # Print stats
    stats = debug_monitor.get_stats()
    print("Debug Stats:")
    print(json.dumps(stats, indent=2))
    
    # Test input validation
    try:
        validate_input("test", str, min_length=2, max_length=10)
        print("Input validation passed")
    except (ValueError, TypeError) as e:
        print(f"Input validation failed: {e}")
    
    # Test code analysis
    test_code = '''
def unsafe_function(user_input):
    eval(user_input)
    for i in range(len(items)):
        result += items[i]
    '''
    
    analyzer = CodeAnalyzer()
    security_issues = analyzer.find_security_issues(test_code)
    performance_issues = analyzer.find_performance_issues(test_code)
    
    print("Security Issues:")
    for issue in security_issues:
        print(f"  Line {issue['line']}: {issue['message']}")
    
    print("Performance Issues:")
    for issue in performance_issues:
        print(f"  Line {issue['line']}: {issue['message']}")

if __name__ == "__main__":
    test_debug_utilities()
        self.log_file = log_file
        self.error_counts = {}
        self.setup_logging()
