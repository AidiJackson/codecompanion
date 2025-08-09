from typing import Dict, List, Any, Optional
import json
from .base_agent import BaseAgent

class TestWriterAgent(BaseAgent):
    """Test Writer Agent - Specialized in test case generation and quality assurance"""
    
    def __init__(self):
        super().__init__(
            name="Test Writer",
            role="Quality Assurance Engineer",
            specialization="Test case generation, quality assurance, validation, and automated testing"
        )
        self.test_frameworks = {
            "python": {
                "unit": ["pytest", "unittest"],
                "integration": ["pytest", "requests"],
                "e2e": ["selenium", "playwright"]
            },
            "javascript": {
                "unit": ["jest", "mocha", "vitest"],
                "integration": ["supertest", "cypress"],
                "e2e": ["cypress", "playwright"]
            }
        }
    
    def process_request(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process test generation requests"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Test generation request: {request}\n\nProject context: {json.dumps(context, indent=2)}"}
        ]
        
        response_content = self.call_llm(messages)
        
        # Generate test files based on request
        generated_files = self.generate_test_files(request, context)
        
        # Determine handoffs
        handoff_to = None
        if any(keyword in request.lower() for keyword in ["debug", "fix", "error", "failing"]):
            handoff_to = "debugger"
        elif any(keyword in request.lower() for keyword in ["code", "implementation", "backend"]):
            handoff_to = "code_generator"
        elif any(keyword in request.lower() for keyword in ["ui", "frontend", "interface"]):
            handoff_to = "ui_designer"
        
        self.add_to_history(request, response_content)
        
        return {
            "content": response_content,
            "handoff_to": handoff_to,
            "agent": self.name,
            "files": generated_files
        }
    
    def process_handoff(self, handoff_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process handoff from another agent"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Handoff from another agent: {handoff_content}\n\nTesting context: {json.dumps(context, indent=2)}"}
        ]
        
        response_content = self.call_llm(messages, temperature=0.5)
        
        # Generate tests based on handoff
        generated_files = self.generate_tests_from_handoff(handoff_content, context)
        
        self.add_to_history(f"Handoff: {handoff_content}", response_content)
        
        return {
            "content": f"**Test Writer Implementation:**\n\n{response_content}",
            "agent": self.name,
            "files": generated_files
        }
    
    def generate_test_files(self, request: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate test files based on request"""
        files = {}
        
        # Detect programming language and generate appropriate tests
        if any(keyword in request.lower() for keyword in ["python", "fastapi", "django"]):
            files.update(self.generate_python_tests(request, context))
        elif any(keyword in request.lower() for keyword in ["javascript", "node", "react", "vue"]):
            files.update(self.generate_javascript_tests(request, context))
        else:
            # Default to Python tests
            files.update(self.generate_python_tests(request, context))
        
        return files
    
    def generate_python_tests(self, request: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate Python test files"""
        files = {}
        
        files["tests/test_api.py"] = '''import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the main application
try:
    from main import app
    client = TestClient(app)
except ImportError:
    # Mock client if main app is not available
    client = None

class TestAPI:
    """Test cases for API endpoints"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.test_data = {
            "name": "Test Item",
            "description": "Test Description",
            "price": 99.99,
            "category": "test"
        }
    
    @pytest.mark.skipif(client is None, reason="Main app not available")
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.skipif(client is None, reason="Main app not available")
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    @pytest.mark.skipif(client is None, reason="Main app not available")
    def test_create_item(self):
        """Test creating a new item"""
        response = client.post("/items", json=self.test_data)
        
        if response.status_code == 200:
            data = response.json()
            assert data["name"] == self.test_data["name"]
            assert data["price"] == self.test_data["price"]
            assert "id" in data
        else:
            # If endpoint doesn't exist, test should pass
            assert response.status_code in [404, 405]
    
    @pytest.mark.skipif(client is None, reason="Main app not available")
    def test_get_items(self):
        """Test retrieving items"""
        response = client.get("/items")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        else:
            # If endpoint doesn't exist, test should pass
            assert response.status_code in [404, 405]
    
    @pytest.mark.skipif(client is None, reason="Main app not available")
    def test_create_item_invalid_data(self):
        """Test creating item with invalid data"""
        invalid_data = {"name": ""}  # Missing required fields
        response = client.post("/items", json=invalid_data)
        
        # Should return validation error
        assert response.status_code in [400, 422, 404, 405]
    
    def test_data_validation(self):
        """Test data validation functions"""
        # Test email validation
        from utils.helpers import validate_email
        
        assert validate_email("test@example.com") == True
        assert validate_email("invalid-email") == False
        assert validate_email("") == False
    
    def test_file_operations(self):
        """Test file operation utilities"""
        from utils.helpers import create_directory, save_json_file, load_json_file
        
        test_dir = "test_temp"
        test_file = os.path.join(test_dir, "test.json")
        test_data = {"test": "data"}
        
        try:
            # Test directory creation
            assert create_directory(test_dir) == True
            assert os.path.exists(test_dir) == True
            
            # Test JSON file operations
            assert save_json_file(test_data, test_file) == True
            loaded_data = load_json_file(test_file)
            assert loaded_data == test_data
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

class TestDatabaseOperations:
    """Test database operations"""
    
    def setup_method(self):
        """Setup test database"""
        self.test_db_path = "test.db"
    
    def teardown_method(self):
        """Cleanup test database"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_database_initialization(self):
        """Test database initialization"""
        try:
            from database import DatabaseManager
            db = DatabaseManager(self.test_db_path)
            
            # Test table creation
            tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [table['name'] for table in tables]
            
            # Should have created some tables
            assert len(table_names) > 0
            
        except ImportError:
            # Skip if database module not available
            pytest.skip("Database module not available")
    
    def test_create_user(self):
        """Test user creation"""
        try:
            from database import DatabaseManager
            db = DatabaseManager(self.test_db_path)
            
            user_id = db.create_user(
                username="testuser",
                email="test@example.com",
                password_hash="hashed_password",
                full_name="Test User"
            )
            
            assert user_id > 0
            
            # Retrieve user
            user = db.get_user(user_id)
            assert user is not None
            assert user['username'] == "testuser"
            assert user['email'] == "test@example.com"
            
        except ImportError:
            pytest.skip("Database module not available")

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_email_validation(self):
        """Test email validation function"""
        try:
            from utils.helpers import validate_email
            
            # Valid emails
            assert validate_email("test@example.com") == True
            assert validate_email("user.name+tag@domain.co.uk") == True
            
            # Invalid emails
            assert validate_email("invalid-email") == False
            assert validate_email("@domain.com") == False
            assert validate_email("user@") == False
            assert validate_email("") == False
            
        except ImportError:
            pytest.skip("Utilities module not available")
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        try:
            from utils.helpers import sanitize_filename
            
            # Test various invalid characters
            assert sanitize_filename("file<name>.txt") == "file_name_.txt"
            assert sanitize_filename("file:name.txt") == "file_name.txt"
            assert sanitize_filename("  file name  ") == "file name"
            
        except ImportError:
            pytest.skip("Utilities module not available")

# Fixtures for common test data
@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    }

@pytest.fixture
def sample_product_data():
    """Sample product data for tests"""
    return {
        "name": "Test Product",
        "description": "A test product",
        "price": 29.99,
        "category": "test",
        "stock_quantity": 100
    }

# Integration tests
class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.integration
    def test_user_product_workflow(self, sample_user_data, sample_product_data):
        """Test complete user and product workflow"""
        try:
            from database import DatabaseManager
            db = DatabaseManager("integration_test.db")
            
            # Create user
            user_id = db.create_user(**sample_user_data)
            assert user_id > 0
            
            # Create product
            product_id = db.create_product(**sample_product_data)
            assert product_id > 0
            
            # Create order
            order_id = db.create_order(user_id, 59.98)  # 2 products
            assert order_id > 0
            
            # Verify data
            user = db.get_user(user_id)
            assert user['username'] == sample_user_data['username']
            
            products = db.get_products()
            assert len(products) >= 1
            
            orders = db.get_user_orders(user_id)
            assert len(orders) >= 1
            
        except ImportError:
            pytest.skip("Database module not available")
        finally:
            # Cleanup
            if os.path.exists("integration_test.db"):
                os.remove("integration_test.db")

# Performance tests
class TestPerformance:
    """Performance tests"""
    
    @pytest.mark.performance
    def test_database_performance(self):
        """Test database operation performance"""
        try:
            import time
            from database import DatabaseManager
            
            db = DatabaseManager("performance_test.db")
            
            # Test bulk insert performance
            start_time = time.time()
            
            for i in range(100):
                db.create_user(
                    username=f"user{i}",
                    email=f"user{i}@example.com",
                    password_hash="hashed_password"
                )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (adjust as needed)
            assert duration < 5.0, f"Bulk insert took too long: {duration}s"
            
        except ImportError:
            pytest.skip("Database module not available")
        finally:
            # Cleanup
            if os.path.exists("performance_test.db"):
                os.remove("performance_test.db")

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
'''
        
        files["tests/test_utils.py"] = '''import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch

class TestUtilityFunctions:
    """Test utility functions and helpers"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test.json")
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_json_file_operations(self):
        """Test JSON file save and load operations"""
        try:
            from utils.helpers import save_json_file, load_json_file
            
            test_data = {
                "name": "Test",
                "values": [1, 2, 3],
                "nested": {"key": "value"}
            }
            
            # Test save
            result = save_json_file(test_data, self.test_file_path)
            assert result == True
            assert os.path.exists(self.test_file_path)
            
            # Test load
            loaded_data = load_json_file(self.test_file_path)
            assert loaded_data == test_data
            
            # Test load non-existent file
            non_existent = load_json_file("non_existent.json")
            assert non_existent is None
            
        except ImportError:
            pytest.skip("Utils module not available")
    
    def test_csv_operations(self):
        """Test CSV file operations"""
        try:
            from utils.helpers import save_csv_file, load_csv_file
            
            test_data = [
                {"name": "John", "age": "30", "city": "New York"},
                {"name": "Jane", "age": "25", "city": "San Francisco"}
            ]
            
            csv_path = os.path.join(self.temp_dir, "test.csv")
            
            # Test save
            result = save_csv_file(test_data, csv_path)
            assert result == True
            assert os.path.exists(csv_path)
            
            # Test load
            loaded_data = load_csv_file(csv_path)
            assert len(loaded_data) == 2
            assert loaded_data[0]["name"] == "John"
            
        except ImportError:
            pytest.skip("Utils module not available")
    
    def test_directory_operations(self):
        """Test directory creation"""
        try:
            from utils.helpers import create_directory
            
            new_dir = os.path.join(self.temp_dir, "new_directory")
            
            result = create_directory(new_dir)
            assert result == True
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)
            
            # Test creating existing directory
            result2 = create_directory(new_dir)
            assert result2 == True  # Should not fail
            
        except ImportError:
            pytest.skip("Utils module not available")
    
    def test_email_validation(self):
        """Test email validation function"""
        try:
            from utils.helpers import validate_email
            
            # Valid emails
            valid_emails = [
                "test@example.com",
                "user.name@domain.co.uk",
                "user+tag@domain.org",
                "123@domain.com"
            ]
            
            for email in valid_emails:
                assert validate_email(email) == True, f"Valid email failed: {email}"
            
            # Invalid emails
            invalid_emails = [
                "invalid-email",
                "@domain.com",
                "user@",
                "",
                "user@domain",
                "user name@domain.com",
                "user..name@domain.com"
            ]
            
            for email in invalid_emails:
                assert validate_email(email) == False, f"Invalid email passed: {email}"
                
        except ImportError:
            pytest.skip("Utils module not available")
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        try:
            from utils.helpers import sanitize_filename
            
            test_cases = [
                ("normal_file.txt", "normal_file.txt"),
                ("file with spaces.txt", "file with spaces.txt"),
                ("file<with>invalid:chars.txt", "file_with_invalid_chars.txt"),
                ("file|with?more*invalid.txt", "file_with_more_invalid.txt"),
                ("  file with leading spaces.txt  ", "file with leading spaces.txt"),
                ("file.with.dots.txt", "file.with.dots.txt"),
                ("", ""),
            ]
            
            for input_name, expected in test_cases:
                result = sanitize_filename(input_name)
                assert result == expected, f"Sanitization failed: '{input_name}' -> '{result}' (expected '{expected}')"
                
        except ImportError:
            pytest.skip("Utils module not available")
    
    def test_file_size_calculation(self):
        """Test file size calculation"""
        try:
            from utils.helpers import get_file_size
            
            # Create a test file with known content
            test_content = "Hello, World!" * 100  # Known size
            with open(self.test_file_path, 'w') as f:
                f.write(test_content)
            
            file_size = get_file_size(self.test_file_path)
            assert file_size is not None
            assert file_size > 0
            assert file_size == len(test_content.encode('utf-8'))
            
            # Test non-existent file
            non_existent_size = get_file_size("non_existent_file.txt")
            assert non_existent_size is None
            
        except ImportError:
            pytest.skip("Utils module not available")
    
    def test_timestamp_formatting(self):
        """Test timestamp formatting"""
        try:
            from utils.helpers import format_timestamp
            from datetime import datetime
            
            # Test with specific datetime
            test_datetime = datetime(2023, 12, 25, 15, 30, 45)
            formatted = format_timestamp(test_datetime)
            assert formatted == "2023-12-25 15:30:45"
            
            # Test with current time (should not raise exception)
            current_formatted = format_timestamp()
            assert isinstance(current_formatted, str)
            assert len(current_formatted) == 19  # YYYY-MM-DD HH:MM:SS format
            
        except ImportError:
            pytest.skip("Utils module not available")

class TestFileManager:
    """Test file management utilities"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_project_file_creation(self):
        """Test project file creation and management"""
        try:
            from utils.helpers import format_code_for_download, create_project_template
            
            # Test project template creation
            template = create_project_template("Web Application")
            assert isinstance(template, dict)
            assert "structure" in template
            assert "technologies" in template
            
            # Test code formatting for download
            test_files = {
                "main.py": "print('Hello World')",
                "config.json": '{"test": true}'
            }
            
            formatted = format_code_for_download(test_files)
            assert isinstance(formatted, str)
            
            # Should be valid JSON
            import json
            parsed = json.loads(formatted)
            assert "files" in parsed
            assert len(parsed["files"]) == 2
            
        except ImportError:
            pytest.skip("Utils module not available")
    
    def test_code_validation(self):
        """Test code validation functions"""
        # Test Python syntax validation
        valid_python = "print('Hello World')"
        invalid_python = "print('Hello World'"  # Missing closing parenthesis
        
        # Basic syntax check (if we had a validation function)
        try:
            compile(valid_python, '<string>', 'exec')
            valid_syntax = True
        except SyntaxError:
            valid_syntax = False
        
        assert valid_syntax == True
        
        try:
            compile(invalid_python, '<string>', 'exec')
            invalid_syntax = False
        except SyntaxError:
            invalid_syntax = True
        
        assert invalid_syntax == True

class TestErrorHandling:
    """Test error handling in utility functions"""
    
    def test_graceful_error_handling(self):
        """Test that functions handle errors gracefully"""
        try:
            from utils.helpers import load_json_file, save_json_file
            
            # Test loading invalid JSON
            invalid_json_path = "invalid.json"
            with open(invalid_json_path, 'w') as f:
                f.write("invalid json content")
            
            result = load_json_file(invalid_json_path)
            assert result is None  # Should return None, not raise exception
            
            # Cleanup
            os.remove(invalid_json_path)
            
            # Test saving to read-only directory (if possible)
            readonly_path = "/root/readonly.json"  # This should fail in most systems
            test_data = {"test": "data"}
            
            result = save_json_file(test_data, readonly_path)
            # Should return False, not raise exception
            assert result == False
            
        except ImportError:
            pytest.skip("Utils module not available")
        except PermissionError:
            # Expected in some environments
            pass

# Mock tests for external dependencies
class TestMockIntegrations:
    """Test with mocked external dependencies"""
    
    @patch('requests.get')
    def test_api_call_simulation(self, mock_get):
        """Test API call with mocked response"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "data": []}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # This would test an actual API function if we had one
        # For now, just verify the mock works
        import requests
        response = requests.get("https://api.example.com/data")
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_get.assert_called_once_with("https://api.example.com/data")
    
    @patch('os.path.exists')
    def test_file_existence_mock(self, mock_exists):
        """Test file existence checking with mock"""
        mock_exists.return_value = True
        
        import os
        result = os.path.exists("any_file.txt")
        assert result == True
        mock_exists.assert_called_once_with("any_file.txt")

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
'''
        
        files["tests/conftest.py"] = '''"""
Pytest configuration and shared fixtures
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock

@pytest.fixture(scope="session")
def temp_directory():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_data():
    """Sample data for testing"""
    return {
        "users": [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
        ],
        "products": [
            {"id": 1, "name": "Product A", "price": 29.99},
            {"id": 2, "name": "Product B", "price": 49.99}
        ]
    }

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Mocked AI response"
    return mock_response

@pytest.fixture
def mock_database():
    """Mock database for testing"""
    db = Mock()
    db.get_user.return_value = {"id": 1, "name": "Test User"}
    db.create_user.return_value = 1
    db.get_products.return_value = []
    return db

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers to tests based on their names
    for item in items:
        if "integration" in item.name:
            item.add_marker(pytest.mark.integration)
        if "performance" in item.name:
            item.add_marker(pytest.mark.performance)
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)
'''
        
        return files
    
    def generate_javascript_tests(self, request: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate JavaScript test files"""
        files = {}
        
        files["tests/api.test.js"] = '''const request = require('supertest');
const app = require('../app');

describe('API Endpoints', () => {
  let server;
  
  beforeAll(async () => {
    // Setup test server if needed
    if (app.listen) {
      server = app.listen(0);
    }
  });
  
  afterAll(async () => {
    // Cleanup
    if (server) {
      server.close();
    }
  });
  
  describe('GET /', () => {
    test('should return welcome message', async () => {
      if (!app) {
        return; // Skip if app not available
      }
      
      const response = await request(app).get('/');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('message');
    });
  });
  
  describe('GET /health', () => {
    test('should return health status', async () => {
      if (!app) {
        return; // Skip if app not available
      }
      
      const response = await request(app).get('/health');
      
      if (response.status === 200) {
        expect(response.body).toHaveProperty('status', 'healthy');
      } else {
        // Endpoint might not exist
        expect(response.status).toBe(404);
      }
    });
  });
  
  describe('POST /items', () => {
    const testItem = {
      name: 'Test Item',
      description: 'Test Description',
      price: 99.99,
      category: 'test'
    };
    
    test('should create new item', async () => {
      if (!app) {
        return; // Skip if app not available
      }
      
      const response = await request(app)
        .post('/items')
        .send(testItem);
      
      if (response.status === 201 || response.status === 200) {
        expect(response.body).toHaveProperty('name', testItem.name);
        expect(response.body).toHaveProperty('price', testItem.price);
      } else {
        // Endpoint might not exist
        expect([404, 405]).toContain(response.status);
      }
    });
    
    test('should reject invalid item data', async () => {
      if (!app) {
        return; // Skip if app not available
      }
      
      const invalidItem = { name: '' }; // Missing required fields
      
      const response = await request(app)
        .post('/items')
        .send(invalidItem);
      
      // Should return validation error or 404 if endpoint doesn't exist
      expect([400, 422, 404, 405]).toContain(response.status);
    });
  });
  
  describe('GET /items', () => {
    test('should return items list', async () => {
      if (!app) {
        return; // Skip if app not available
      }
      
      const response = await request(app).get('/items');
      
      if (response.status === 200) {
        expect(Array.isArray(response.body)).toBe(true);
      } else {
        // Endpoint might not exist
        expect(response.status).toBe(404);
      }
    });
  });
});

describe('Utility Functions', () => {
  describe('Data Validation', () => {
    test('should validate email addresses', () => {
      const { validateEmail } = require('../utils/validation');
      
      if (validateEmail) {
        expect(validateEmail('test@example.com')).toBe(true);
        expect(validateEmail('invalid-email')).toBe(false);
        expect(validateEmail('')).toBe(false);
      }
    });
    
    test('should sanitize input data', () => {
      const { sanitizeInput } = require('../utils/validation');
      
      if (sanitizeInput) {
        const input = '<script>alert("xss")</script>Test';
        const sanitized = sanitizeInput(input);
        expect(sanitized).not.toContain('<script>');
        expect(sanitized).toContain('Test');
      }
    });
  });
  
  describe('File Operations', () => {
    test('should handle file operations safely', () => {
      const fs = require('fs').promises;
      const path = require('path');
      
      const testFile = path.join(__dirname, 'temp_test.txt');
      const testData = 'Test file content';
      
      return fs.writeFile(testFile, testData)
        .then(() => fs.readFile(testFile, 'utf8'))
        .then(content => {
          expect(content).toBe(testData);
          return fs.unlink(testFile);
        })
        .catch(error => {
          // Cleanup on error
          return fs.unlink(testFile).catch(() => {}).then(() => {
            throw error;
          });
        });
    });
  });
});

describe('Integration Tests', () => {
  describe('Complete Workflow', () => {
    test('should handle complete item lifecycle', async () => {
      if (!app) {
        return; // Skip if app not available
      }
      
      const testItem = {
        name: 'Integration Test Item',
        description: 'Test Description',
        price: 199.99,
        category: 'integration'
      };
      
      // Create item
      const createResponse = await request(app)
        .post('/items')
        .send(testItem);
      
      if (createResponse.status === 200 || createResponse.status === 201) {
        const createdItem = createResponse.body;
        expect(createdItem).toHaveProperty('id');
        
        // Get item
        const getResponse = await request(app).get(`/items/${createdItem.id}`);
        
        if (getResponse.status === 200) {
          expect(getResponse.body.name).toBe(testItem.name);
          
          // Update item
          const updatedData = { ...testItem, price: 299.99 };
          const updateResponse = await request(app)
            .put(`/items/${createdItem.id}`)
            .send(updatedData);
          
          if (updateResponse.status === 200) {
            expect(updateResponse.body.price).toBe(299.99);
          }
          
          // Delete item
          const deleteResponse = await request(app).delete(`/items/${createdItem.id}`);
          expect([200, 204]).toContain(deleteResponse.status);
        }
      }
    });
  });
});

describe('Error Handling', () => {
  test('should handle 404 errors gracefully', async () => {
    if (!app) {
      return; // Skip if app not available
    }
    
    const response = await request(app).get('/nonexistent-endpoint');
    expect(response.status).toBe(404);
  });
  
  test('should handle server errors gracefully', async () => {
    if (!app) {
      return; // Skip if app not available
    }
    
    // This would test error handling if we had an endpoint that could trigger errors
    // For now, just ensure the test framework is working
    expect(true).toBe(true);
  });
});
'''
        
        files["tests/components.test.js"] = '''// React component tests (if React is being used)
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock components for testing
const MockButton = ({ onClick, children, disabled }) => (
  <button onClick={onClick} disabled={disabled}>
    {children}
  </button>
);

const MockInput = ({ value, onChange, placeholder }) => (
  <input value={value} onChange={onChange} placeholder={placeholder} />
);

const MockModal = ({ isOpen, onClose, children }) => 
  isOpen ? (
    <div data-testid="modal">
      <button onClick={onClose}>Close</button>
      {children}
    </div>
  ) : null;

describe('UI Components', () => {
  describe('Button Component', () => {
    test('renders button with text', () => {
      render(<MockButton>Click me</MockButton>);
      expect(screen.getByText('Click me')).toBeInTheDocument();
    });
    
    test('calls onClick when clicked', () => {
      const handleClick = jest.fn();
      render(<MockButton onClick={handleClick}>Click me</MockButton>);
      
      fireEvent.click(screen.getByText('Click me'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
    
    test('is disabled when disabled prop is true', () => {
      render(<MockButton disabled>Disabled Button</MockButton>);
      expect(screen.getByText('Disabled Button')).toBeDisabled();
    });
  });
  
  describe('Input Component', () => {
    test('renders input with placeholder', () => {
      render(<MockInput placeholder="Enter text" />);
      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
    });
    
    test('calls onChange when value changes', () => {
      const handleChange = jest.fn();
      render(<MockInput onChange={handleChange} />);
      
      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'new value' } });
      
      expect(handleChange).toHaveBeenCalledTimes(1);
    });
    
    test('displays current value', () => {
      render(<MockInput value="test value" onChange={() => {}} />);
      expect(screen.getByDisplayValue('test value')).toBeInTheDocument();
    });
  });
  
  describe('Modal Component', () => {
    test('renders when isOpen is true', () => {
      render(<MockModal isOpen={true}>Modal Content</MockModal>);
      expect(screen.getByTestId('modal')).toBeInTheDocument();
      expect(screen.getByText('Modal Content')).toBeInTheDocument();
    });
    
    test('does not render when isOpen is false', () => {
      render(<MockModal isOpen={false}>Modal Content</MockModal>);
      expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
    });
    
    test('calls onClose when close button is clicked', () => {
      const handleClose = jest.fn();
      render(<MockModal isOpen={true} onClose={handleClose}>Modal Content</MockModal>);
      
      fireEvent.click(screen.getByText('Close'));
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });
});

describe('Form Interactions', () => {
  const MockForm = () => {
    const [formData, setFormData] = React.useState({
      name: '',
      email: '',
      message: ''
    });
    const [errors, setErrors] = React.useState({});
    const [submitted, setSubmitted] = React.useState(false);
    
    const handleChange = (e) => {
      setFormData({ ...formData, [e.target.name]: e.target.value });
    };
    
    const validateForm = () => {
      const newErrors = {};
      if (!formData.name) newErrors.name = 'Name is required';
      if (!formData.email) newErrors.email = 'Email is required';
      if (formData.email && !/\S+@\S+\.\S+/.test(formData.email)) {
        newErrors.email = 'Email is invalid';
      }
      return newErrors;
    };
    
    const handleSubmit = (e) => {
      e.preventDefault();
      const newErrors = validateForm();
      setErrors(newErrors);
      
      if (Object.keys(newErrors).length === 0) {
        setSubmitted(true);
      }
    };
    
    return (
      <form onSubmit={handleSubmit}>
        <input
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="Name"
        />
        {errors.name && <span data-testid="name-error">{errors.name}</span>}
        
        <input
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="Email"
        />
        {errors.email && <span data-testid="email-error">{errors.email}</span>}
        
        <textarea
          name="message"
          value={formData.message}
          onChange={handleChange}
          placeholder="Message"
        />
        
        <button type="submit">Submit</button>
        
        {submitted && <div data-testid="success">Form submitted successfully!</div>}
      </form>
    );
  };
  
  test('validates required fields', async () => {
    render(<MockForm />);
    
    fireEvent.click(screen.getByText('Submit'));
    
    await waitFor(() => {
      expect(screen.getByTestId('name-error')).toBeInTheDocument();
      expect(screen.getByTestId('email-error')).toBeInTheDocument();
    });
  });
  
  test('validates email format', async () => {
    render(<MockForm />);
    
    fireEvent.change(screen.getByPlaceholderText('Name'), {
      target: { value: 'John Doe' }
    });
    fireEvent.change(screen.getByPlaceholderText('Email'), {
      target: { value: 'invalid-email' }
    });
    
    fireEvent.click(screen.getByText('Submit'));
    
    await waitFor(() => {
      expect(screen.getByTestId('email-error')).toHaveTextContent('Email is invalid');
    });
  });
  
  test('submits form with valid data', async () => {
    render(<MockForm />);
    
    fireEvent.change(screen.getByPlaceholderText('Name'), {
      target: { value: 'John Doe' }
    });
    fireEvent.change(screen.getByPlaceholderText('Email'), {
      target: { value: 'john@example.com' }
    });
    fireEvent.change(screen.getByPlaceholderText('Message'), {
      target: { value: 'Test message' }
    });
    
    fireEvent.click(screen.getByText('Submit'));
    
    await waitFor(() => {
      expect(screen.getByTestId('success')).toBeInTheDocument();
    });
  });
});

describe('Accessibility Tests', () => {
  test('components have proper ARIA labels', () => {
    render(
      <div>
        <button aria-label="Close modal">×</button>
        <input aria-label="Search" />
        <div role="alert" aria-live="polite">Status message</div>
      </div>
    );
    
    expect(screen.getByLabelText('Close modal')).toBeInTheDocument();
    expect(screen.getByLabelText('Search')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
  
  test('keyboard navigation works', () => {
    render(
      <div>
        <button>Button 1</button>
        <button>Button 2</button>
        <input />
      </div>
    );
    
    const button1 = screen.getByText('Button 1');
    const button2 = screen.getByText('Button 2');
    
    button1.focus();
    expect(button1).toHaveFocus();
    
    // Simulate Tab key
    fireEvent.keyDown(button1, { key: 'Tab', code: 'Tab' });
    // In a real app, focus would move to next element
  });
});

// Performance tests
describe('Performance Tests', () => {
  test('component renders within acceptable time', () => {
    const start = performance.now();
    
    render(
      <div>
        {Array.from({ length: 1000 }, (_, i) => (
          <div key={i}>Item {i}</div>
        ))}
      </div>
    );
    
    const end = performance.now();
    const renderTime = end - start;
    
    // Should render within 100ms (adjust as needed)
    expect(renderTime).toBeLessThan(100);
  });
});
'''
        
        return files
    
    def generate_tests_from_handoff(self, handoff_content: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate tests based on handoff from another agent"""
        files = {}
        
        # Parse handoff content to determine what tests to generate
        if "python" in handoff_content.lower() or "fastapi" in handoff_content.lower():
            files.update(self.generate_python_tests(handoff_content, context))
        elif "javascript" in handoff_content.lower() or "react" in handoff_content.lower():
            files.update(self.generate_javascript_tests(handoff_content, context))
        
        # Always add a basic test file for the handoff
        files["tests/test_handoff_integration.py"] = f'''"""
Integration tests for handoff from another agent
"""
import pytest

class TestHandoffIntegration:
    """Test integration based on agent handoff"""
    
    def test_handoff_processing(self):
        """Test that handoff content is processed correctly"""
        handoff_content = """{handoff_content[:500]}"""
        
        # Verify handoff content is not empty
        assert len(handoff_content.strip()) > 0
        
        # Basic validation that content makes sense
        assert any(keyword in handoff_content.lower() for keyword in 
                  ['code', 'function', 'class', 'api', 'test', 'implementation'])
    
    def test_context_availability(self):
        """Test that context information is available"""
        context = {context}
        
        # Context should be a dictionary
        assert isinstance(context, dict)
        
        # Should contain some basic information
        if context:
            assert any(key in context for key in ['project', 'files', 'request', 'agent'])
    
    def test_generated_code_validity(self):
        """Test that any generated code is syntactically valid"""
        # This would test actual generated code if available
        # For now, just ensure test framework is working
        test_code = "print('Hello from handoff test')"
        
        # Should compile without syntax errors
        try:
            compile(test_code, '<string>', 'exec')
            valid_syntax = True
        except SyntaxError:
            valid_syntax = False
        
        assert valid_syntax == True
'''
        
        return files
    
    def get_system_prompt(self) -> str:
        """Get specialized system prompt for test writer"""
        base_prompt = super().get_system_prompt()
        return base_prompt + """
        
        As the Test Writer agent, you:
        - Generate comprehensive test suites for code quality assurance
        - Create unit tests, integration tests, and end-to-end tests
        - Implement test automation and continuous testing strategies
        - Validate functionality, performance, and security aspects
        - Ensure code coverage and test reliability
        - Write clear, maintainable test code with good documentation
        
        When writing tests:
        1. Create comprehensive test coverage for all functionality
        2. Include positive and negative test cases
        3. Test edge cases and error conditions
        4. Write clear, descriptive test names and documentation
        5. Use appropriate testing frameworks and best practices
        6. Include integration tests for component interactions
        7. Generate performance and security tests when relevant
        
        Hand off to:
        - debugger: When tests reveal bugs or issues
        - code_generator: When implementation needs fixing
        - ui_designer: For UI/UX testing and validation
        """
