"""
Simple smoke tests for artifact schema validation using Pydantic.

Basic tests to verify schemas work correctly with minimal valid data.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pydantic import ValidationError

try:
    from schemas.artifacts import (
        ArtifactBase, 
        CodePatch, 
        ArtifactType,
        SpecDoc,
        create_artifact_from_dict
    )
except ImportError as e:
    pytest.skip(f"Cannot import artifact schemas: {e}", allow_module_level=True)


class TestCodePatchSchema:
    """Basic smoke tests for CodePatch schema"""
    
    def test_code_patch_minimal_valid(self):
        """Test CodePatch with minimal required fields"""
        
        patch_data = {
            "artifact_id": "test-001",
            "created_by": "test_agent", 
            "title": "Test patch",
            "description": "A test patch",
            "files_changed": [{"path": "test.py", "action": "created", "lines_added": 1, "lines_removed": 0}],
            "diff_unified": "--- /dev/null\n+++ b/test.py\n@@ -0,0 +1 @@\n+print('test')",
            "language": "python"
        }
        
        patch = CodePatch(**patch_data)
        
        assert patch.artifact_id == "test-001"
        assert patch.created_by == "test_agent"
        assert patch.title == "Test patch"
        assert patch.language == "python"
        assert len(patch.files_changed) == 1
        assert patch.files_changed[0]["path"] == "test.py"
    
    def test_code_patch_missing_required_field(self):
        """Test that CodePatch fails with missing required fields"""
        
        incomplete_data = {
            "artifact_id": "incomplete",
            "created_by": "test_agent",
            "title": "Incomplete patch"
            # Missing description, files_changed, diff_unified, language
        }
        
        with pytest.raises(ValidationError):
            CodePatch(**incomplete_data)
    
    def test_code_patch_invalid_files_changed_format(self):
        """Test that CodePatch fails with invalid files_changed format"""
        
        invalid_data = {
            "artifact_id": "invalid-files",
            "created_by": "test_agent",
            "title": "Invalid files test",
            "description": "Test invalid files format",
            "files_changed": ["just_a_string"],  # Should be list of dicts
            "diff_unified": "--- test",
            "language": "python"
        }
        
        with pytest.raises(ValidationError):
            CodePatch(**invalid_data)


class TestSpecDocSchema:
    """Basic smoke tests for SpecDoc schema"""
    
    def test_spec_doc_minimal_valid(self):
        """Test SpecDoc with minimal required fields"""
        
        spec_data = {
            "artifact_id": "spec-001",
            "created_by": "spec_agent",
            "title": "Test Specification",
            "objective": "Test the spec schema",
            "requirements": [{"id": "REQ-001", "description": "Basic requirement"}],
            "acceptance_criteria": ["Schema validates correctly"]
        }
        
        spec = SpecDoc(**spec_data)
        
        assert spec.artifact_id == "spec-001"
        assert spec.created_by == "spec_agent"
        assert spec.title == "Test Specification"
        assert spec.artifact_type == ArtifactType.SPEC_DOC
        assert len(spec.requirements) == 1
        assert spec.requirements[0]["id"] == "REQ-001"
    
    def test_spec_doc_missing_required_field(self):
        """Test that SpecDoc fails with missing required fields"""
        
        incomplete_data = {
            "artifact_id": "incomplete-spec",
            "created_by": "spec_agent",
            "title": "Incomplete spec"
            # Missing objective, requirements, acceptance_criteria
        }
        
        with pytest.raises(ValidationError):
            SpecDoc(**incomplete_data)


class TestFactoryFunction:
    """Test artifact factory function"""
    
    def test_create_code_patch_via_factory(self):
        """Test creating CodePatch through factory function"""
        
        patch_data = {
            "artifact_id": "factory-patch",
            "created_by": "factory_agent",
            "title": "Factory test patch",
            "description": "Created via factory",
            "files_changed": [{"path": "factory.py", "action": "created", "lines_added": 1, "lines_removed": 0}],
            "diff_unified": "--- /dev/null\n+++ b/factory.py\n@@ -0,0 +1 @@\n+# factory test",
            "language": "python",
            "type": "code"  # Factory function uses this field
        }
        
        artifact = create_artifact_from_dict(patch_data)
        
        assert isinstance(artifact, CodePatch)
        assert artifact.artifact_id == "factory-patch"
        assert artifact.language == "python"
    
    def test_create_spec_doc_via_factory(self):
        """Test creating SpecDoc through factory function"""
        
        spec_data = {
            "artifact_id": "factory-spec",
            "created_by": "factory_agent",
            "title": "Factory spec",
            "objective": "Test factory creation",
            "requirements": [{"id": "REQ-001", "description": "Factory requirement"}],
            "acceptance_criteria": ["Factory works"]
            # No type field, should default to base artifact (SpecDoc)
        }
        
        artifact = create_artifact_from_dict(spec_data)
        
        assert isinstance(artifact, ArtifactBase)
        assert artifact.artifact_id == "factory-spec"


class TestArtifactTypeEnum:
    """Test ArtifactType enum validation"""
    
    def test_valid_artifact_types(self):
        """Test that valid artifact types are accepted"""
        
        valid_spec = {
            "artifact_id": "enum-test",
            "artifact_type": "spec_doc",  # Valid enum value
            "created_by": "enum_agent",
            "title": "Enum test",
            "objective": "Test enum validation",
            "requirements": [{"id": "REQ-001", "description": "Enum requirement"}],
            "acceptance_criteria": ["Enum works"]
        }
        
        spec = SpecDoc(**valid_spec)
        assert spec.artifact_type == ArtifactType.SPEC_DOC
    
    def test_invalid_artifact_type(self):
        """Test that invalid artifact types are rejected"""
        
        invalid_spec = {
            "artifact_id": "invalid-enum",
            "artifact_type": "invalid_type",  # Invalid enum value
            "created_by": "enum_agent",
            "title": "Invalid enum test",
            "objective": "Test invalid enum",
            "requirements": [{"id": "REQ-001", "description": "Test requirement"}],
            "acceptance_criteria": ["Should fail"]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SpecDoc(**invalid_spec)
        
        error_str = str(exc_info.value).lower()
        assert "invalid_type" in error_str or "enum" in error_str


def test_comprehensive_smoke_test():
    """Comprehensive smoke test covering core functionality"""
    
    # Test 1: Create valid CodePatch
    patch_data = {
        "artifact_id": "smoke-patch",
        "created_by": "smoke_agent",
        "title": "Smoke test patch",
        "description": "Comprehensive smoke test",
        "files_changed": [{"path": "smoke.py", "action": "created", "lines_added": 2, "lines_removed": 0}],
        "diff_unified": "--- /dev/null\n+++ b/smoke.py\n@@ -0,0 +1,2 @@\n+def smoke_test():\n+    return True",
        "language": "python"
    }
    
    patch = CodePatch(**patch_data)
    assert patch.artifact_id == "smoke-patch"
    
    # Test 2: Create valid SpecDoc
    spec_data = {
        "artifact_id": "smoke-spec",
        "created_by": "smoke_agent",
        "title": "Smoke test specification",
        "objective": "Verify smoke test functionality",
        "requirements": [{"id": "SMOKE-001", "description": "System must pass smoke tests"}],
        "acceptance_criteria": ["All smoke tests pass", "No validation errors"]
    }
    
    spec = SpecDoc(**spec_data)
    assert spec.artifact_id == "smoke-spec"
    assert spec.artifact_type == ArtifactType.SPEC_DOC
    
    # Test 3: Verify serialization works
    patch_json = patch.model_dump_json()
    assert isinstance(patch_json, str)
    
    # Test 4: Verify factory function works  
    factory_artifact = create_artifact_from_dict({
        **patch_data,
        "type": "code"
    })
    assert isinstance(factory_artifact, CodePatch)
    
    print("✅ All comprehensive smoke tests passed")


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])