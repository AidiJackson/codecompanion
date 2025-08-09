"""
Utility functions and helpers for the multi-agent development system
"""
import os
import json
import csv
import re
import zipfile
import io
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid
import hashlib
import base64

def validate_email(email: str) -> bool:
    """Validate email address format"""
    if not email or not isinstance(email, str):
        return False
    
    # Simple but effective email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    if not filename:
        return ""
    
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure it's not empty after sanitization
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized

def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """Save data to JSON file"""
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            create_directory(directory)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        return False

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file and return parsed data"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {file_path}")
        return None
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None

def save_csv_file(data: List[Dict[str, Any]], file_path: str) -> bool:
    """Save data to CSV file"""
    if not data:
        return False
    
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            create_directory(directory)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"Error saving CSV file: {e}")
        return False

def load_csv_file(file_path: str) -> List[Dict[str, str]]:
    """Load CSV file and return list of dictionaries"""
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return []

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
    except (FileNotFoundError, OSError):
        return None

def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Format timestamp for display"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def generate_file_hash(content: str) -> str:
    """Generate SHA-256 hash of file content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def format_code_for_download(project_files: Dict[str, str]) -> str:
    """Format project files for download as JSON"""
    download_data = {
        "project_info": {
            "name": "Generated Project",
            "created_at": datetime.now().isoformat(),
            "total_files": len(project_files),
            "generator": "CodeCompanion Multi-Agent System"
        },
        "files": {}
    }
    
    for filename, content in project_files.items():
        download_data["files"][filename] = {
            "content": content,
            "size_bytes": len(content.encode('utf-8')),
            "hash": generate_file_hash(content),
            "created_at": datetime.now().isoformat()
        }
    
    return json.dumps(download_data, indent=2)

def create_project_zip(project_files: Dict[str, str]) -> bytes:
    """Create a ZIP file from project files"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in project_files.items():
            # Sanitize filename for ZIP
            safe_filename = sanitize_filename(filename)
            zip_file.writestr(safe_filename, content)
        
        # Add metadata file
        metadata = {
            "created_by": "CodeCompanion Multi-Agent System",
            "created_at": datetime.now().isoformat(),
            "total_files": len(project_files),
            "file_list": list(project_files.keys())
        }
        zip_file.writestr("project_metadata.json", json.dumps(metadata, indent=2))
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def create_project_template(template_type: str) -> Dict[str, Any]:
    """Create project template based on type"""
    templates = {
        "Web Application": {
            "structure": [
                "frontend/",
                "frontend/src/",
                "frontend/public/",
                "backend/",
                "backend/api/",
                "backend/models/",
                "database/",
                "tests/",
                "docs/"
            ],
            "technologies": [
                "React/Vue.js (Frontend)",
                "Node.js/Python (Backend)",
                "PostgreSQL/MongoDB (Database)",
                "REST API",
                "Authentication"
            ],
            "phases": [
                "Requirements Analysis",
                "System Design",
                "Frontend Development",
                "Backend Development",
                "Database Design",
                "API Integration",
                "Testing",
                "Deployment"
            ],
            "estimated_duration": "4-8 weeks",
            "complexity": "Medium to High"
        },
        
        "API Service": {
            "structure": [
                "src/",
                "src/routes/",
                "src/middleware/",
                "src/models/",
                "src/controllers/",
                "tests/",
                "docs/",
                "config/",
                "scripts/"
            ],
            "technologies": [
                "FastAPI/Express.js",
                "Database (SQL/NoSQL)",
                "Authentication & Authorization",
                "API Documentation",
                "Rate Limiting",
                "Logging & Monitoring"
            ],
            "phases": [
                "API Design",
                "Core Implementation",
                "Authentication Setup",
                "Database Integration",
                "Testing & Validation",
                "Documentation",
                "Deployment"
            ],
            "estimated_duration": "2-4 weeks",
            "complexity": "Medium"
        },
        
        "Data Pipeline": {
            "structure": [
                "data/",
                "data/raw/",
                "data/processed/",
                "processing/",
                "processing/ingestion/",
                "processing/transformation/",
                "models/",
                "output/",
                "config/",
                "scripts/",
                "tests/"
            ],
            "technologies": [
                "Python/Apache Spark",
                "Apache Airflow/Prefect",
                "Data Storage (S3, HDFS)",
                "Databases (PostgreSQL, MongoDB)",
                "Monitoring & Alerting",
                "Docker & Kubernetes"
            ],
            "phases": [
                "Data Source Analysis",
                "Pipeline Architecture",
                "Data Ingestion",
                "Data Transformation",
                "Data Validation",
                "Monitoring Setup",
                "Testing & Optimization"
            ],
            "estimated_duration": "3-6 weeks",
            "complexity": "Medium to High"
        },
        
        "Mobile App": {
            "structure": [
                "src/",
                "src/components/",
                "src/screens/",
                "src/navigation/",
                "src/services/",
                "src/utils/",
                "assets/",
                "tests/",
                "docs/"
            ],
            "technologies": [
                "React Native/Flutter",
                "State Management (Redux/MobX)",
                "API Integration",
                "Local Storage",
                "Push Notifications",
                "App Store Deployment"
            ],
            "phases": [
                "UI/UX Design",
                "Component Development",
                "Navigation Setup",
                "API Integration",
                "Testing (Unit & E2E)",
                "Performance Optimization",
                "App Store Submission"
            ],
            "estimated_duration": "6-12 weeks",
            "complexity": "High"
        },
        
        "Custom Project": {
            "structure": [
                "src/",
                "tests/",
                "docs/",
                "config/",
                "assets/"
            ],
            "technologies": [
                "To be determined based on requirements"
            ],
            "phases": [
                "Requirements Gathering",
                "Technology Selection",
                "Architecture Design",
                "Implementation",
                "Testing",
                "Documentation",
                "Deployment"
            ],
            "estimated_duration": "Variable",
            "complexity": "Variable"
        }
    }
    
    template = templates.get(template_type, templates["Custom Project"])
    
    # Add common metadata
    template.update({
        "template_type": template_type,
        "created_at": datetime.now().isoformat(),
        "version": "1.0",
        "common_files": [
            "README.md",
            "requirements.txt / package.json",
            ".gitignore",
            "LICENSE",
            "CHANGELOG.md"
        ]
    })
    
    return template

def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """Extract code blocks from markdown text"""
    code_blocks = []
    
    # Pattern to match fenced code blocks
    pattern = r'```(\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for i, (language, code) in enumerate(matches):
        code_blocks.append({
            "id": f"code_block_{i}",
            "language": language or "text",
            "code": code.strip(),
            "line_count": len(code.strip().split('\n'))
        })
    
    return code_blocks

def validate_project_structure(files: Dict[str, str]) -> Dict[str, Any]:
    """Validate project structure and suggest improvements"""
    validation = {
        "valid": True,
        "warnings": [],
        "suggestions": [],
        "file_analysis": {}
    }
    
    # Check for essential files
    essential_files = ["README.md"]
    missing_essential = [f for f in essential_files if f not in files]
    
    if missing_essential:
        validation["warnings"].append(f"Missing essential files: {', '.join(missing_essential)}")
    
    # Analyze file types
    file_types = {}
    for filename in files.keys():
        ext = os.path.splitext(filename)[1].lower()
        file_types[ext] = file_types.get(ext, 0) + 1
    
    validation["file_analysis"]["file_types"] = file_types
    
    # Check for configuration files
    config_files = [f for f in files.keys() if any(
        keyword in f.lower() for keyword in ['config', 'settings', '.env', 'requirements', 'package.json']
    )]
    
    if not config_files:
        validation["suggestions"].append("Consider adding configuration files (config.py, .env, etc.)")
    
    # Check for test files
    test_files = [f for f in files.keys() if 'test' in f.lower()]
    
    if not test_files:
        validation["suggestions"].append("Consider adding test files for better code quality")
    
    # Check for documentation
    doc_files = [f for f in files.keys() if any(
        keyword in f.lower() for keyword in ['readme', 'doc', 'guide']
    )]
    
    if len(doc_files) < 2:
        validation["suggestions"].append("Consider adding more documentation files")
    
    return validation

def parse_agent_response(response: str) -> Dict[str, Any]:
    """Parse agent response and extract structured information"""
    parsed = {
        "content": response,
        "code_blocks": extract_code_blocks(response),
        "suggestions": [],
        "next_steps": [],
        "technologies_mentioned": []
    }
    
    # Extract suggestions (lines starting with suggestions indicators)
    suggestion_patterns = [
        r'(?:suggestion|recommend|consider|should):\s*(.+)',
        r'💡\s*(.+)',
        r'[\-\*]\s*(.+)(?:suggestion|recommendation)'
    ]
    
    for pattern in suggestion_patterns:
        matches = re.findall(pattern, response, re.IGNORECASE | re.MULTILINE)
        parsed["suggestions"].extend(matches)
    
    # Extract next steps
    next_step_patterns = [
        r'(?:next step|next|todo|action):\s*(.+)',
        r'🔄\s*(.+)',
        r'[\-\*]\s*(.+)(?:next|step|action)'
    ]
    
    for pattern in next_step_patterns:
        matches = re.findall(pattern, response, re.IGNORECASE | re.MULTILINE)
        parsed["next_steps"].extend(matches)
    
    # Extract technology mentions
    technologies = [
        'python', 'javascript', 'react', 'vue', 'angular', 'node.js', 'fastapi', 
        'django', 'flask', 'express', 'mongodb', 'postgresql', 'mysql', 'redis',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp'
    ]
    
    for tech in technologies:
        if tech.lower() in response.lower():
            parsed["technologies_mentioned"].append(tech)
    
    return parsed

def calculate_project_complexity(files: Dict[str, str], features: List[str] = None) -> Dict[str, Any]:
    """Calculate estimated project complexity"""
    complexity_score = 0
    factors = []
    
    # File count factor
    file_count = len(files)
    if file_count > 20:
        complexity_score += 3
        factors.append("High file count")
    elif file_count > 10:
        complexity_score += 2
        factors.append("Medium file count")
    else:
        complexity_score += 1
        factors.append("Low file count")
    
    # Code size factor
    total_lines = sum(len(content.split('\n')) for content in files.values())
    if total_lines > 5000:
        complexity_score += 3
        factors.append("Large codebase")
    elif total_lines > 1000:
        complexity_score += 2
        factors.append("Medium codebase")
    else:
        complexity_score += 1
        factors.append("Small codebase")
    
    # Technology diversity
    file_extensions = set(os.path.splitext(f)[1].lower() for f in files.keys())
    tech_diversity = len(file_extensions)
    
    if tech_diversity > 5:
        complexity_score += 2
        factors.append("High technology diversity")
    elif tech_diversity > 3:
        complexity_score += 1
        factors.append("Medium technology diversity")
    
    # Feature complexity
    if features:
        feature_keywords = ['api', 'database', 'authentication', 'real-time', 'ai', 'ml']
        complex_features = [f for f in features if any(keyword in f.lower() for keyword in feature_keywords)]
        complexity_score += len(complex_features)
        if complex_features:
            factors.append(f"Complex features: {', '.join(complex_features)}")
    
    # Determine complexity level
    if complexity_score >= 8:
        level = "High"
        estimated_time = "6-12 weeks"
    elif complexity_score >= 5:
        level = "Medium"
        estimated_time = "3-6 weeks"
    else:
        level = "Low"
        estimated_time = "1-3 weeks"
    
    return {
        "complexity_level": level,
        "complexity_score": complexity_score,
        "factors": factors,
        "estimated_time": estimated_time,
        "metrics": {
            "file_count": file_count,
            "total_lines": total_lines,
            "technology_diversity": tech_diversity
        }
    }

def generate_project_summary(project_data: Dict[str, Any]) -> str:
    """Generate a comprehensive project summary"""
    files = project_data.get("files", {})
    project_info = project_data.get("project_info", {})
    
    summary = f"""# Project Summary

## Overview
- **Project Name**: {project_info.get('name', 'Unnamed Project')}
- **Created**: {project_info.get('created_at', 'Unknown')}
- **Total Files**: {len(files)}

## File Structure
"""
    
    # Group files by directory
    directories = {}
    for filepath in files.keys():
        if '/' in filepath:
            dir_name = filepath.split('/')[0]
            if dir_name not in directories:
                directories[dir_name] = []
            directories[dir_name].append(filepath)
        else:
            if 'root' not in directories:
                directories['root'] = []
            directories['root'].append(filepath)
    
    for dir_name, dir_files in directories.items():
        summary += f"\n### {dir_name}/\n"
        for file in sorted(dir_files):
            file_size = len(files[file].encode('utf-8'))
            summary += f"- {file} ({file_size:,} bytes)\n"
    
    # Add complexity analysis
    complexity = calculate_project_complexity(files)
    summary += f"""
## Complexity Analysis
- **Level**: {complexity['complexity_level']}
- **Estimated Time**: {complexity['estimated_time']}
- **Key Factors**: {', '.join(complexity['factors'])}

## Metrics
- **Total Lines of Code**: {complexity['metrics']['total_lines']:,}
- **Technology Diversity**: {complexity['metrics']['technology_diversity']} different file types
"""
    
    return summary

# Global utility functions for easy access
def safe_execute(func, *args, default=None, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Safe execute failed: {e}")
        return default

def ensure_list(value: Any) -> List[Any]:
    """Ensure value is a list"""
    if isinstance(value, list):
        return value
    elif value is None:
        return []
    else:
        return [value]

def ensure_dict(value: Any) -> Dict[str, Any]:
    """Ensure value is a dictionary"""
    if isinstance(value, dict):
        return value
    else:
        return {}

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def merge_dictionaries(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later ones taking precedence"""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result
