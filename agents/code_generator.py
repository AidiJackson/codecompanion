from typing import Dict, List, Any, Optional
import json
from .base_agent import BaseAgent

class CodeGeneratorAgent(BaseAgent):
    """Code Generator Agent - Specialized in backend development and algorithm implementation"""
    
    def __init__(self):
        super().__init__(
            name="Code Generator",
            role="Backend Developer",
            specialization="Backend development, algorithms, APIs, database design, and server-side logic"
        )
        self.code_templates = {
            "python_api": {
                "framework": "FastAPI",
                "files": ["main.py", "models.py", "routes.py", "database.py"]
            },
            "javascript_api": {
                "framework": "Express.js",
                "files": ["app.js", "routes.js", "models.js", "config.js"]
            },
            "python_script": {
                "framework": "Python",
                "files": ["main.py", "utils.py", "config.py"]
            }
        }
    
    def process_request(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process code generation requests"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Code generation request: {request}\n\nProject context: {json.dumps(context, indent=2)}"}
        ]
        
        response_content = self.call_llm(messages)
        
        # Generate actual code files based on request
        generated_files = self.generate_code_files(request, context)
        
        # Determine handoffs
        handoff_to = None
        if any(keyword in request.lower() for keyword in ["test", "testing", "validate"]):
            handoff_to = "test_writer"
        elif any(keyword in request.lower() for keyword in ["frontend", "ui", "interface"]):
            handoff_to = "ui_designer"
        elif any(keyword in request.lower() for keyword in ["debug", "fix", "error"]):
            handoff_to = "debugger"
        
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
            {"role": "user", "content": f"Handoff from another agent: {handoff_content}\n\nImplementation context: {json.dumps(context, indent=2)}"}
        ]
        
        response_content = self.call_llm(messages, temperature=0.5)
        
        # Generate code based on handoff
        generated_files = self.generate_code_from_handoff(handoff_content, context)
        
        self.add_to_history(f"Handoff: {handoff_content}", response_content)
        
        return {
            "content": f"**Code Generator Implementation:**\n\n{response_content}",
            "agent": self.name,
            "files": generated_files
        }
    
    def generate_code_files(self, request: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate code files based on request"""
        files = {}
        
        # Detect project type and generate appropriate code
        if any(keyword in request.lower() for keyword in ["api", "fastapi", "backend"]):
            files.update(self.generate_fastapi_code(request))
        elif any(keyword in request.lower() for keyword in ["script", "python", "automation"]):
            files.update(self.generate_python_script(request))
        elif any(keyword in request.lower() for keyword in ["database", "db", "model"]):
            files.update(self.generate_database_code(request))
        else:
            files.update(self.generate_generic_code(request))
        
        return files
    
    def generate_fastapi_code(self, request: str) -> Dict[str, str]:
        """Generate FastAPI application code"""
        files = {}
        
        files["main.py"] = '''from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Generated API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float
    category: str

# In-memory storage (replace with database)
items_db = []

@app.get("/")
async def root():
    return {"message": "Welcome to the Generated API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    item.id = len(items_db) + 1
    items_db.append(item)
    return item

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, updated_item: Item):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            updated_item.id = item_id
            items_db[i] = updated_item
            return updated_item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            del items_db[i]
            return {"message": "Item deleted successfully"}
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        
        files["models.py"] = '''from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ItemStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class BaseItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: str = Field(..., min_length=1, max_length=50)

class ItemCreate(BaseItem):
    price: float = Field(..., gt=0)
    status: ItemStatus = ItemStatus.ACTIVE

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[ItemStatus] = None

class Item(BaseItem):
    id: int
    price: float
    status: ItemStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ItemResponse(BaseModel):
    items: List[Item]
    total: int
    page: int
    size: int
'''
        
        files["database.py"] = '''import sqlite3
from typing import List, Optional
from contextlib import contextmanager
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_item(self, item_data: dict) -> int:
        """Create a new item and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO items (name, description, price, category, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                item_data['name'],
                item_data.get('description'),
                item_data['price'],
                item_data['category'],
                item_data.get('status', 'active')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_item(self, item_id: int) -> Optional[dict]:
        """Get item by ID"""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
            return dict(row) if row else None
    
    def get_items(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """Get all items with pagination"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM items ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def update_item(self, item_id: int, item_data: dict) -> bool:
        """Update item and return success status"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE items 
                SET name = ?, description = ?, price = ?, category = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                item_data['name'],
                item_data.get('description'),
                item_data['price'],
                item_data['category'],
                item_data.get('status', 'active'),
                item_id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_item(self, item_id: int) -> bool:
        """Delete item and return success status"""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
            conn.commit()
            return cursor.rowcount > 0

# Global database instance
db = DatabaseManager()
'''
        
        return files
    
    def generate_python_script(self, request: str) -> Dict[str, str]:
        """Generate Python script code"""
        files = {}
        
        files["main.py"] = '''#!/usr/bin/env python3
"""
Generated Python Script
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScriptProcessor:
    """Main script processor class"""
    
    def __init__(self):
        self.start_time = datetime.now()
        logger.info("Script processor initialized")
    
    def process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process input data and return results"""
        results = []
        
        for item in data:
            try:
                # Add processing logic here
                processed_item = {
                    **item,
                    'processed_at': datetime.now().isoformat(),
                    'status': 'processed'
                }
                results.append(processed_item)
                logger.info(f"Processed item: {item.get('id', 'unknown')}")
            
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                continue
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """Save results to file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def run(self):
        """Main execution method"""
        logger.info("Starting script execution")
        
        # Sample data for demonstration
        sample_data = [
            {'id': 1, 'name': 'Item 1', 'value': 100},
            {'id': 2, 'name': 'Item 2', 'value': 200},
            {'id': 3, 'name': 'Item 3', 'value': 300}
        ]
        
        # Process data
        results = self.process_data(sample_data)
        
        # Save results
        output_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.save_results(results, output_file)
        
        execution_time = datetime.now() - self.start_time
        logger.info(f"Script completed in {execution_time.total_seconds():.2f} seconds")

if __name__ == "__main__":
    processor = ScriptProcessor()
    processor.run()
'''
        
        files["utils.py"] = '''"""
Utility functions for the script
"""

import os
import json
import csv
from typing import Any, Dict, List, Optional
from datetime import datetime

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file and return parsed data"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {file_path}")
        return None

def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """Save data to JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        return False

def load_csv_file(file_path: str) -> List[Dict[str, str]]:
    """Load CSV file and return list of dictionaries"""
    try:
        with open(file_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []

def save_csv_file(data: List[Dict[str, Any]], file_path: str) -> bool:
    """Save data to CSV file"""
    if not data:
        return False
    
    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"Error saving CSV file: {e}")
        return False

def create_directory(dir_path: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory: {e}")
        return False

def get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except FileNotFoundError:
        return None

def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Format timestamp for display"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def validate_email(email: str) -> bool:
    """Simple email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    import re
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    return sanitized
'''
        
        return files
    
    def generate_database_code(self, request: str) -> Dict[str, str]:
        """Generate database-related code"""
        files = {}
        
        files["database_manager.py"] = '''import sqlite3
import json
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from datetime import datetime

class DatabaseManager:
    """Comprehensive database management class"""
    
    def __init__(self, db_path: str = "application.db"):
        self.db_path = db_path
        self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def initialize_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            # Products table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2) NOT NULL,
                    category_id INTEGER,
                    stock_quantity INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            """)
            
            # Categories table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    parent_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES categories (id)
                )
            """)
            
            # Orders table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_amount DECIMAL(10,2) NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
    
    # User operations
    def create_user(self, username: str, email: str, password_hash: str, full_name: str = None) -> int:
        """Create a new user"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (?, ?, ?, ?)
            """, (username, email, password_hash, full_name))
            conn.commit()
            return cursor.lastrowid
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            return dict(row) if row else None
    
    # Product operations
    def create_product(self, name: str, price: float, description: str = None, category_id: int = None) -> int:
        """Create a new product"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO products (name, description, price, category_id)
                VALUES (?, ?, ?, ?)
            """, (name, description, price, category_id))
            conn.commit()
            return cursor.lastrowid
    
    def get_products(self, limit: int = 50, offset: int = 0, category_id: int = None) -> List[Dict]:
        """Get products with optional filtering"""
        with self.get_connection() as conn:
            if category_id:
                rows = conn.execute("""
                    SELECT p.*, c.name as category_name 
                    FROM products p 
                    LEFT JOIN categories c ON p.category_id = c.id 
                    WHERE p.category_id = ? AND p.is_active = 1
                    ORDER BY p.created_at DESC LIMIT ? OFFSET ?
                """, (category_id, limit, offset)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT p.*, c.name as category_name 
                    FROM products p 
                    LEFT JOIN categories c ON p.category_id = c.id 
                    WHERE p.is_active = 1
                    ORDER BY p.created_at DESC LIMIT ? OFFSET ?
                """, (limit, offset)).fetchall()
            return [dict(row) for row in rows]
    
    def update_product_stock(self, product_id: int, quantity_change: int) -> bool:
        """Update product stock quantity"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE products 
                SET stock_quantity = stock_quantity + ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (quantity_change, product_id))
            conn.commit()
            return cursor.rowcount > 0
    
    # Category operations
    def create_category(self, name: str, description: str = None, parent_id: int = None) -> int:
        """Create a new category"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO categories (name, description, parent_id)
                VALUES (?, ?, ?)
            """, (name, description, parent_id))
            conn.commit()
            return cursor.lastrowid
    
    def get_categories(self) -> List[Dict]:
        """Get all categories"""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
            return [dict(row) for row in rows]
    
    # Order operations
    def create_order(self, user_id: int, total_amount: float) -> int:
        """Create a new order"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO orders (user_id, total_amount)
                VALUES (?, ?)
            """, (user_id, total_amount))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        """Get orders for a specific user"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
            """, (user_id,)).fetchall()
            return [dict(row) for row in rows]
    
    # Utility methods
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute custom query and return results"""
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """Get table schema information"""
        with self.get_connection() as conn:
            rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            return [dict(row) for row in rows]
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            with self.get_connection() as source:
                backup = sqlite3.connect(backup_path)
                source.backup(backup)
                backup.close()
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False
'''
        
        return files
    
    def generate_generic_code(self, request: str) -> Dict[str, str]:
        """Generate generic code based on request"""
        files = {}
        
        files["application.py"] = '''"""
Generated Application Code
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Application:
    """Main application class"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.start_time = datetime.now()
        self.initialize()
    
    def initialize(self):
        """Initialize application components"""
        logger.info("Initializing application...")
        
        # Load configuration
        self.load_configuration()
        
        # Initialize components
        self.setup_components()
        
        logger.info("Application initialized successfully")
    
    def load_configuration(self):
        """Load application configuration"""
        config_file = self.config.get('config_file', 'config.json')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                logger.info(f"Configuration loaded from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        
        # Set default values
        self.config.setdefault('debug', False)
        self.config.setdefault('max_workers', 4)
        self.config.setdefault('timeout', 30)
    
    def setup_components(self):
        """Setup application components"""
        # Initialize data storage
        self.data_store = {}
        
        # Initialize processors
        self.processors = []
        
        # Initialize validators
        self.validators = []
    
    def process_data(self, data: Any) -> Any:
        """Process input data through all processors"""
        result = data
        
        for processor in self.processors:
            try:
                result = processor.process(result)
            except Exception as e:
                logger.error(f"Processor {processor.__class__.__name__} failed: {e}")
                if not self.config.get('continue_on_error', False):
                    raise
        
        return result
    
    def validate_data(self, data: Any) -> bool:
        """Validate data using all validators"""
        for validator in self.validators:
            try:
                if not validator.validate(data):
                    logger.warning(f"Validation failed: {validator.__class__.__name__}")
                    return False
            except Exception as e:
                logger.error(f"Validator {validator.__class__.__name__} error: {e}")
                return False
        
        return True
    
    def store_data(self, key: str, data: Any):
        """Store data in application storage"""
        self.data_store[key] = {
            'data': data,
            'timestamp': datetime.now(),
            'type': type(data).__name__
        }
        logger.info(f"Data stored with key: {key}")
    
    def retrieve_data(self, key: str) -> Optional[Any]:
        """Retrieve data from application storage"""
        stored_item = self.data_store.get(key)
        if stored_item:
            return stored_item['data']
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get application statistics"""
        uptime = datetime.now() - self.start_time
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'data_items_stored': len(self.data_store),
            'processors_count': len(self.processors),
            'validators_count': len(self.validators),
            'config_items': len(self.config),
            'start_time': self.start_time.isoformat()
        }
    
    def shutdown(self):
        """Graceful application shutdown"""
        logger.info("Shutting down application...")
        
        # Cleanup resources
        self.data_store.clear()
        self.processors.clear()
        self.validators.clear()
        
        uptime = datetime.now() - self.start_time
        logger.info(f"Application shutdown complete. Uptime: {uptime.total_seconds():.2f} seconds")

class DataProcessor:
    """Base data processor class"""
    
    def process(self, data: Any) -> Any:
        """Process data - to be overridden by subclasses"""
        return data

class DataValidator:
    """Base data validator class"""
    
    def validate(self, data: Any) -> bool:
        """Validate data - to be overridden by subclasses"""
        return True

if __name__ == "__main__":
    # Example usage
    app = Application({
        'debug': True,
        'max_workers': 2
    })
    
    # Store some sample data
    app.store_data('sample', {'message': 'Hello World', 'value': 42})
    
    # Retrieve and display statistics
    stats = app.get_statistics()
    print(f"Application Statistics: {json.dumps(stats, indent=2)}")
    
    # Graceful shutdown
    app.shutdown()
'''
        
        return files
    
    def generate_code_from_handoff(self, handoff_content: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate code based on handoff from another agent"""
        files = {}
        
        # Parse handoff content to determine what to generate
        if "api" in handoff_content.lower():
            files.update(self.generate_fastapi_code(handoff_content))
        elif "database" in handoff_content.lower():
            files.update(self.generate_database_code(handoff_content))
        else:
            files.update(self.generate_generic_code(handoff_content))
        
        return files
    
    def get_system_prompt(self) -> str:
        """Get specialized system prompt for code generator"""
        base_prompt = super().get_system_prompt()
        return base_prompt + """
        
        As the Code Generator agent, you:
        - Write clean, efficient, and well-documented code
        - Follow best practices and coding standards
        - Generate complete, functional code files
        - Include proper error handling and logging
        - Create scalable and maintainable solutions
        - Provide code examples and implementation details
        
        When generating code:
        1. Always provide complete, runnable code
        2. Include necessary imports and dependencies
        3. Add comprehensive comments and documentation
        4. Follow PEP 8 for Python code
        5. Include error handling and validation
        6. Create modular and reusable components
        
        Hand off to:
        - ui_designer: For frontend integration
        - test_writer: For testing the generated code
        - debugger: If issues are detected in the code
        """
