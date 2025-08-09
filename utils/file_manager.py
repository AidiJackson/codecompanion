"""
File management utilities for the multi-agent development system
"""
import os
import shutil
import tempfile
import zipfile
import io
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import json
import mimetypes
import hashlib
import base64
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileManager:
    """Comprehensive file management system for projects"""
    
    def __init__(self, base_directory: str = None):
        self.base_directory = base_directory or tempfile.gettempdir()
        self.project_files: Dict[str, Dict[str, Any]] = {}
        self.file_history: List[Dict[str, Any]] = []
        
    def create_project_structure(self, project_name: str, template_type: str = "Custom Project") -> Dict[str, Any]:
        """Create project directory structure"""
        from .helpers import create_project_template
        
        template = create_project_template(template_type)
        project_path = os.path.join(self.base_directory, project_name)
        
        try:
            # Create base project directory
            os.makedirs(project_path, exist_ok=True)
            
            # Create directory structure
            created_dirs = []
            for directory in template.get("structure", []):
                dir_path = os.path.join(project_path, directory)
                os.makedirs(dir_path, exist_ok=True)
                created_dirs.append(directory)
            
            # Create common files
            common_files = {
                "README.md": self._generate_readme(project_name, template),
                ".gitignore": self._generate_gitignore(template_type),
                "project_info.json": json.dumps({
                    "name": project_name,
                    "template": template_type,
                    "created_at": datetime.now().isoformat(),
                    "structure": template.get("structure", []),
                    "technologies": template.get("technologies", [])
                }, indent=2)
            }
            
            # Write common files
            for filename, content in common_files.items():
                file_path = os.path.join(project_path, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            self._log_file_operation("create_project", project_name, {
                "template": template_type,
                "directories": created_dirs,
                "files": list(common_files.keys())
            })
            
            return {
                "project_path": project_path,
                "directories_created": created_dirs,
                "files_created": list(common_files.keys()),
                "template_info": template
            }
            
        except Exception as e:
            logger.error(f"Failed to create project structure: {e}")
            return {"error": str(e)}
    
    def add_file(self, 
                filepath: str, 
                content: str, 
                project_name: str = None,
                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add or update a file in the project"""
        
        file_info = {
            "filepath": filepath,
            "content": content,
            "size": len(content.encode('utf-8')),
            "hash": hashlib.sha256(content.encode('utf-8')).hexdigest(),
            "created_at": datetime.now().isoformat(),
            "project_name": project_name,
            "metadata": metadata or {},
            "mime_type": mimetypes.guess_type(filepath)[0] or "text/plain"
        }
        
        # Store in memory
        self.project_files[filepath] = file_info
        
        # Write to disk if project directory exists
        if project_name:
            project_path = os.path.join(self.base_directory, project_name)
            if os.path.exists(project_path):
                full_path = os.path.join(project_path, filepath)
                
                # Ensure directory exists
                directory = os.path.dirname(full_path)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                
                try:
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    file_info["disk_path"] = full_path
                    
                except Exception as e:
                    logger.warning(f"Failed to write file to disk: {e}")
        
        self._log_file_operation("add_file", filepath, {
            "size": file_info["size"],
            "project": project_name
        })
        
        return file_info
    
    def get_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Get file information and content"""
        return self.project_files.get(filepath)
    
    def update_file(self, 
                   filepath: str, 
                   new_content: str,
                   update_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update existing file content"""
        
        if filepath not in self.project_files:
            return {"error": "File not found"}
        
        old_info = self.project_files[filepath].copy()
        
        # Update file info
        self.project_files[filepath].update({
            "content": new_content,
            "size": len(new_content.encode('utf-8')),
            "hash": hashlib.sha256(new_content.encode('utf-8')).hexdigest(),
            "modified_at": datetime.now().isoformat(),
            "version": old_info.get("version", 1) + 1
        })
        
        if update_metadata:
            self.project_files[filepath]["metadata"].update(update_metadata)
        
        # Update disk file if it exists
        if "disk_path" in old_info:
            try:
                with open(old_info["disk_path"], 'w', encoding='utf-8') as f:
                    f.write(new_content)
            except Exception as e:
                logger.warning(f"Failed to update file on disk: {e}")
        
        self._log_file_operation("update_file", filepath, {
            "old_size": old_info["size"],
            "new_size": self.project_files[filepath]["size"],
            "version": self.project_files[filepath]["version"]
        })
        
        return self.project_files[filepath]
    
    def delete_file(self, filepath: str) -> bool:
        """Delete a file from the project"""
        if filepath not in self.project_files:
            return False
        
        file_info = self.project_files[filepath]
        
        # Delete from disk if it exists
        if "disk_path" in file_info:
            try:
                os.remove(file_info["disk_path"])
            except Exception as e:
                logger.warning(f"Failed to delete file from disk: {e}")
        
        # Remove from memory
        del self.project_files[filepath]
        
        self._log_file_operation("delete_file", filepath, {
            "size": file_info["size"]
        })
        
        return True
    
    def list_files(self, 
                  project_name: str = None,
                  file_type: str = None,
                  sort_by: str = "created_at") -> List[Dict[str, Any]]:
        """List files with optional filtering"""
        
        files = []
        for filepath, file_info in self.project_files.items():
            # Filter by project
            if project_name and file_info.get("project_name") != project_name:
                continue
            
            # Filter by file type
            if file_type:
                if file_type.startswith('.'):
                    if not filepath.endswith(file_type):
                        continue
                else:
                    if file_type.lower() not in file_info.get("mime_type", "").lower():
                        continue
            
            files.append({
                "filepath": filepath,
                "size": file_info["size"],
                "created_at": file_info["created_at"],
                "modified_at": file_info.get("modified_at"),
                "mime_type": file_info["mime_type"],
                "project_name": file_info.get("project_name"),
                "version": file_info.get("version", 1)
            })
        
        # Sort files
        if sort_by in ["created_at", "modified_at", "size"]:
            files.sort(key=lambda x: x.get(sort_by, ""), reverse=True)
        elif sort_by == "name":
            files.sort(key=lambda x: x["filepath"])
        
        return files
    
    def create_archive(self, 
                      files: Dict[str, str] = None,
                      project_name: str = None,
                      format_type: str = "zip") -> bytes:
        """Create archive from files"""
        
        # Use provided files or all project files
        if files is None:
            if project_name:
                files = {
                    fp: info["content"] 
                    for fp, info in self.project_files.items()
                    if info.get("project_name") == project_name
                }
            else:
                files = {fp: info["content"] for fp, info in self.project_files.items()}
        
        if format_type.lower() == "zip":
            return self._create_zip_archive(files, project_name)
        else:
            raise ValueError(f"Unsupported archive format: {format_type}")
    
    def _create_zip_archive(self, files: Dict[str, str], project_name: str = None) -> bytes:
        """Create ZIP archive from files"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add files
            for filepath, content in files.items():
                # Sanitize filepath for ZIP
                safe_path = filepath.replace('\\', '/').lstrip('/')
                zip_file.writestr(safe_path, content)
            
            # Add metadata
            metadata = {
                "created_by": "CodeCompanion Multi-Agent System",
                "created_at": datetime.now().isoformat(),
                "project_name": project_name,
                "total_files": len(files),
                "total_size": sum(len(content.encode('utf-8')) for content in files.values()),
                "file_list": list(files.keys())
            }
            
            zip_file.writestr("_metadata.json", json.dumps(metadata, indent=2))
        
        zip_buffer.seek(0)
        archive_data = zip_buffer.getvalue()
        
        self._log_file_operation("create_archive", project_name or "unknown", {
            "format": "zip",
            "files_count": len(files),
            "archive_size": len(archive_data)
        })
        
        return archive_data
    
    def extract_archive(self, 
                       archive_data: bytes, 
                       project_name: str,
                       format_type: str = "zip") -> Dict[str, Any]:
        """Extract files from archive"""
        
        if format_type.lower() == "zip":
            return self._extract_zip_archive(archive_data, project_name)
        else:
            raise ValueError(f"Unsupported archive format: {format_type}")
    
    def _extract_zip_archive(self, archive_data: bytes, project_name: str) -> Dict[str, Any]:
        """Extract ZIP archive"""
        extracted_files = {}
        metadata = None
        
        try:
            with zipfile.ZipFile(io.BytesIO(archive_data), 'r') as zip_file:
                for file_info in zip_file.filelist():
                    filename = file_info.filename
                    
                    # Skip directories
                    if filename.endswith('/'):
                        continue
                    
                    # Read file content
                    content = zip_file.read(filename).decode('utf-8')
                    
                    # Handle metadata file
                    if filename == "_metadata.json":
                        try:
                            metadata = json.loads(content)
                        except json.JSONDecodeError:
                            pass
                        continue
                    
                    # Add file to project
                    self.add_file(filename, content, project_name, {
                        "extracted_from_archive": True,
                        "original_filename": filename
                    })
                    
                    extracted_files[filename] = content
            
            self._log_file_operation("extract_archive", project_name, {
                "format": "zip",
                "files_extracted": len(extracted_files),
                "metadata": metadata is not None
            })
            
            return {
                "extracted_files": extracted_files,
                "metadata": metadata,
                "files_count": len(extracted_files)
            }
            
        except Exception as e:
            logger.error(f"Failed to extract archive: {e}")
            return {"error": str(e)}
    
    def backup_project(self, project_name: str, backup_path: str = None) -> Dict[str, Any]:
        """Create backup of project files"""
        
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.base_directory, f"{project_name}_backup_{timestamp}.zip")
        
        # Get project files
        project_files = {
            fp: info["content"] 
            for fp, info in self.project_files.items()
            if info.get("project_name") == project_name
        }
        
        if not project_files:
            return {"error": "No files found for project"}
        
        try:
            # Create archive
            archive_data = self.create_archive(project_files, project_name)
            
            # Write to backup file
            with open(backup_path, 'wb') as f:
                f.write(archive_data)
            
            backup_info = {
                "backup_path": backup_path,
                "project_name": project_name,
                "files_count": len(project_files),
                "backup_size": len(archive_data),
                "created_at": datetime.now().isoformat()
            }
            
            self._log_file_operation("backup_project", project_name, backup_info)
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return {"error": str(e)}
    
    def restore_project(self, backup_path: str, project_name: str = None) -> Dict[str, Any]:
        """Restore project from backup"""
        
        if not os.path.exists(backup_path):
            return {"error": "Backup file not found"}
        
        try:
            # Read backup file
            with open(backup_path, 'rb') as f:
                archive_data = f.read()
            
            # Extract archive
            result = self.extract_archive(archive_data, project_name or "restored_project")
            
            self._log_file_operation("restore_project", project_name or "restored", {
                "backup_path": backup_path,
                "files_restored": result.get("files_count", 0)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return {"error": str(e)}
    
    def analyze_project(self, project_name: str = None) -> Dict[str, Any]:
        """Analyze project files and structure"""
        
        # Get project files
        if project_name:
            files = {
                fp: info for fp, info in self.project_files.items()
                if info.get("project_name") == project_name
            }
        else:
            files = self.project_files
        
        if not files:
            return {"error": "No files to analyze"}
        
        analysis = {
            "total_files": len(files),
            "total_size": sum(info["size"] for info in files.values()),
            "file_types": {},
            "directory_structure": {},
            "largest_files": [],
            "language_breakdown": {},
            "code_metrics": {
                "total_lines": 0,
                "code_files": 0,
                "documentation_files": 0,
                "configuration_files": 0
            }
        }
        
        # Analyze each file
        for filepath, file_info in files.items():
            # File type analysis
            ext = os.path.splitext(filepath)[1].lower()
            analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
            
            # Directory structure
            if '/' in filepath:
                directory = os.path.dirname(filepath)
                analysis["directory_structure"][directory] = analysis["directory_structure"].get(directory, 0) + 1
            
            # Language detection
            language = self._detect_language(filepath, file_info["content"])
            if language:
                analysis["language_breakdown"][language] = analysis["language_breakdown"].get(language, 0) + 1
            
            # Code metrics
            lines = len(file_info["content"].split('\n'))
            analysis["code_metrics"]["total_lines"] += lines
            
            if self._is_code_file(filepath):
                analysis["code_metrics"]["code_files"] += 1
            elif self._is_documentation_file(filepath):
                analysis["code_metrics"]["documentation_files"] += 1
            elif self._is_configuration_file(filepath):
                analysis["code_metrics"]["configuration_files"] += 1
            
            # Track largest files
            analysis["largest_files"].append({
                "filepath": filepath,
                "size": file_info["size"],
                "lines": lines
            })
        
        # Sort largest files
        analysis["largest_files"].sort(key=lambda x: x["size"], reverse=True)
        analysis["largest_files"] = analysis["largest_files"][:10]  # Top 10
        
        # Calculate additional metrics
        analysis["average_file_size"] = analysis["total_size"] / analysis["total_files"]
        analysis["code_to_documentation_ratio"] = (
            analysis["code_metrics"]["code_files"] / 
            max(analysis["code_metrics"]["documentation_files"], 1)
        )
        
        return analysis
    
    def get_file_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get file operation history"""
        return self.file_history[-limit:] if self.file_history else []
    
    def cleanup_old_files(self, days_old: int = 30, project_name: str = None):
        """Clean up old files"""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        files_to_remove = []
        for filepath, file_info in self.project_files.items():
            # Filter by project if specified
            if project_name and file_info.get("project_name") != project_name:
                continue
            
            # Check if file is old
            created_at = datetime.fromisoformat(file_info["created_at"]).timestamp()
            if created_at < cutoff_time:
                files_to_remove.append(filepath)
        
        # Remove old files
        for filepath in files_to_remove:
            self.delete_file(filepath)
        
        logger.info(f"Cleaned up {len(files_to_remove)} old files")
        
        return {
            "files_removed": len(files_to_remove),
            "files_cleaned": files_to_remove
        }
    
    def _generate_readme(self, project_name: str, template: Dict[str, Any]) -> str:
        """Generate README.md content"""
        return f"""# {project_name}

## Description
{template.get('template_type', 'Custom')} project generated by CodeCompanion Multi-Agent System.

## Project Structure
{chr(10).join(f"- {dir}" for dir in template.get('structure', []))}

## Technologies
{chr(10).join(f"- {tech}" for tech in template.get('technologies', []))}

## Development Phases
{chr(10).join(f"{i+1}. {phase}" for i, phase in enumerate(template.get('phases', [])))}

## Getting Started
1. Review the project structure and requirements
2. Install necessary dependencies
3. Follow the development phases outlined above
4. Run tests to ensure everything works correctly

## Estimated Duration
{template.get('estimated_duration', 'Variable')}

## Complexity
{template.get('complexity', 'Variable')}

---
Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by CodeCompanion Multi-Agent System
"""
    
    def _generate_gitignore(self, template_type: str) -> str:
        """Generate .gitignore content based on template type"""
        base_ignore = """# General
.DS_Store
.vscode/
.idea/
*.log
*.tmp
*.cache

# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv

# Build outputs
dist/
build/
*.egg-info/
"""
        
        if "Web Application" in template_type:
            base_ignore += """
# Web specific
.next/
out/
.nuxt/
dist/
.cache/
"""
        
        if "Python" in template_type or "API" in template_type:
            base_ignore += """
# Python specific
*.egg
.pytest_cache/
.coverage
htmlcov/
.tox/
"""
        
        return base_ignore
    
    def _detect_language(self, filepath: str, content: str) -> Optional[str]:
        """Detect programming language from file"""
        ext = os.path.splitext(filepath)[1].lower()
        
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React TypeScript',
            '.vue': 'Vue.js',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'SASS',
            '.json': 'JSON',
            '.xml': 'XML',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.bash': 'Bash',
            '.md': 'Markdown',
            '.txt': 'Text',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        
        return language_map.get(ext)
    
    def _is_code_file(self, filepath: str) -> bool:
        """Check if file is a code file"""
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.vue', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt'}
        return os.path.splitext(filepath)[1].lower() in code_extensions
    
    def _is_documentation_file(self, filepath: str) -> bool:
        """Check if file is documentation"""
        doc_extensions = {'.md', '.txt', '.rst', '.doc', '.docx'}
        doc_names = {'readme', 'license', 'changelog', 'contributing', 'docs'}
        
        ext = os.path.splitext(filepath)[1].lower()
        name = os.path.splitext(os.path.basename(filepath))[0].lower()
        
        return ext in doc_extensions or any(doc_name in name for doc_name in doc_names)
    
    def _is_configuration_file(self, filepath: str) -> bool:
        """Check if file is configuration"""
        config_extensions = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'}
        config_names = {'config', 'settings', 'package', 'requirements', 'dockerfile', 'makefile'}
        
        ext = os.path.splitext(filepath)[1].lower()
        name = os.path.splitext(os.path.basename(filepath))[0].lower()
        
        return (ext in config_extensions or 
                any(config_name in name for config_name in config_names) or
                filepath.startswith('.'))
    
    def _log_file_operation(self, operation: str, target: str, details: Dict[str, Any]):
        """Log file operation for history"""
        log_entry = {
            "operation": operation,
            "target": target,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        self.file_history.append(log_entry)
        
        # Keep history limited
        if len(self.file_history) > 1000:
            self.file_history = self.file_history[-500:]
        
        logger.debug(f"File operation: {operation} on {target}")

# Global file manager instance
file_manager = FileManager()

# Helper functions for easy access
def add_project_file(filepath: str, content: str, project_name: str = None) -> Dict[str, Any]:
    """Helper function to add file to project"""
    return file_manager.add_file(filepath, content, project_name)

def get_project_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Helper function to get project file"""
    return file_manager.get_file(filepath)

def create_project_archive(files: Dict[str, str], project_name: str = None) -> bytes:
    """Helper function to create project archive"""
    return file_manager.create_archive(files, project_name)

def analyze_project_files(project_name: str = None) -> Dict[str, Any]:
    """Helper function to analyze project"""
    return file_manager.analyze_project(project_name)
