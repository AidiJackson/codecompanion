"""
Demonstration of the Typed Artifact System with Schema Enforcement.

This script showcases the complete typed artifact system including:
- Artifact creation with strict validation
- Agent handoff protocols
- Conflict detection and resolution
- Quality scoring and lineage tracking
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any

from core.artifact_handler import TypedArtifactHandler
from core.handoff_protocol import AgentHandoff, HandoffRequest, AgentType
from core.conflict_resolver import ConflictResolver
from schemas.artifact_schemas import ArtifactType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_artifact_creation():
    """Demonstrate artifact creation with validation"""
    print("\n=== TYPED ARTIFACT CREATION DEMO ===")
    
    artifact_handler = TypedArtifactHandler()
    
    # Create a SpecDoc artifact
    spec_doc_data = {
        "title": "E-commerce Platform Requirements",
        "objective": "Build a modern e-commerce platform with user authentication, product catalog, and payment processing",
        "scope": "Full-stack web application with admin dashboard and customer portal",
        "requirements": [
            {
                "id": "REQ-001",
                "description": "Users must be able to register, login, and manage their profiles securely",
                "priority": "high"
            },
            {
                "id": "REQ-002", 
                "description": "System must display products with images, descriptions, and pricing",
                "priority": "high"
            }
        ],
        "acceptance_criteria": [
            "User registration takes less than 2 minutes",
            "Product search returns results in under 1 second",
            "Payment processing is PCI compliant"
        ],
        "business_value": "Increase online sales by 40% within 6 months"
    }
    
    result = artifact_handler.create_artifact(
        agent_output=spec_doc_data,
        artifact_type="SpecDoc",
        agent_id="project_manager"
    )
    
    if "error" not in result:
        print(f"✅ SpecDoc created successfully!")
        print(f"   Artifact ID: {result['artifact']['artifact_id']}")
        print(f"   Confidence: {result['confidence_metrics']['overall_confidence']:.2f}")
        print(f"   Quality Score: {result['validation_result']['quality_score']:.2f}")
        return result['artifact']['artifact_id']
    else:
        print(f"❌ SpecDoc creation failed: {result['error_details']}")
        return None


def demo_design_doc_creation(spec_doc_id: str):
    """Create a design document based on the spec"""
    print("\n=== DESIGN DOCUMENT CREATION ===")
    
    artifact_handler = TypedArtifactHandler()
    
    design_doc_data = {
        "title": "E-commerce Platform Architecture",
        "overview": "Microservices architecture with React frontend, Node.js backend, and PostgreSQL database",
        "system_architecture": {
            "style": "microservices",
            "layers": ["presentation", "business", "data"],
            "communication": "REST APIs with JWT authentication"
        },
        "components": [
            {
                "id": "COMP-001",
                "name": "Authentication Service",
                "description": "Handles user registration, login, and JWT token management",
                "responsibilities": ["user auth", "token validation", "password reset"],
                "interfaces": ["REST API", "database"]
            },
            {
                "id": "COMP-002",
                "name": "Product Catalog Service", 
                "description": "Manages product inventory, search, and catalog operations",
                "responsibilities": ["product CRUD", "search", "categories"],
                "interfaces": ["REST API", "database", "search engine"]
            }
        ],
        "design_decisions": [
            {
                "id": "DEC-001",
                "name": "Microservices Architecture",
                "description": "Use microservices for scalability and maintainability",
                "rationale": "Allows independent scaling and deployment of services",
                "alternatives": ["monolith", "modular monolith"],
                "decision": "microservices"
            }
        ],
        "technology_stack": {
            "frontend": "React with TypeScript",
            "backend": "Node.js with Express",
            "database": "PostgreSQL",
            "authentication": "JWT with bcrypt"
        },
        "dependencies": [spec_doc_id] if spec_doc_id else []
    }
    
    result = artifact_handler.create_artifact(
        agent_output=design_doc_data,
        artifact_type="DesignDoc", 
        agent_id="ui_designer"
    )
    
    if "error" not in result:
        print(f"✅ DesignDoc created successfully!")
        print(f"   Artifact ID: {result['artifact']['artifact_id']}")
        print(f"   Confidence: {result['confidence_metrics']['overall_confidence']:.2f}")
        return result['artifact']['artifact_id']
    else:
        print(f"❌ DesignDoc creation failed: {result['error_details']}")
        return None


def demo_code_patch_creation(design_doc_id: str):
    """Create a code patch implementing the design"""
    print("\n=== CODE PATCH CREATION ===")
    
    artifact_handler = TypedArtifactHandler()
    
    code_patch_data = {
        "task_id": "TASK-001",
        "title": "Implement User Authentication Service",
        "description": "Initial implementation of user registration and login endpoints with JWT authentication",
        "base_commit": "abc123def456",
        "files_changed": [
            {
                "path": "src/services/auth.js",
                "action": "added",
                "lines_added": 85,
                "lines_removed": 0,
                "language": "javascript"
            },
            {
                "path": "src/routes/auth.js", 
                "action": "added",
                "lines_added": 45,
                "lines_removed": 0,
                "language": "javascript"
            }
        ],
        "diff_unified": """--- /dev/null
+++ b/src/services/auth.js
@@ -0,0 +1,85 @@
+const bcrypt = require('bcrypt');
+const jwt = require('jsonwebtoken');
+const User = require('../models/User');
+
+class AuthService {
+  async register(userData) {
+    const hashedPassword = await bcrypt.hash(userData.password, 12);
+    const user = new User({
+      ...userData,
+      password: hashedPassword
+    });
+    return await user.save();
+  }
+}""",
        "language": "javascript",
        "impact": ["api", "security", "database"],
        "test_instructions": [
            "Run authentication unit tests",
            "Test user registration endpoint",
            "Verify JWT token generation"
        ],
        "dependencies": [design_doc_id] if design_doc_id else []
    }
    
    result = artifact_handler.create_artifact(
        agent_output=code_patch_data,
        artifact_type="CodePatch",
        agent_id="code_generator"
    )
    
    if "error" not in result:
        print(f"✅ CodePatch created successfully!")
        print(f"   Artifact ID: {result['artifact']['artifact_id']}")
        print(f"   Confidence: {result['confidence_metrics']['overall_confidence']:.2f}")
        return result['artifact']['artifact_id']
    else:
        print(f"❌ CodePatch creation failed: {result['error_details']}")
        return None


def demo_handoff_validation():
    """Demonstrate agent handoff validation"""
    print("\n=== AGENT HANDOFF VALIDATION DEMO ===")
    
    artifact_handler = TypedArtifactHandler()
    handoff_protocol = AgentHandoff(artifact_handler)
    
    # Create some test artifacts first
    spec_id = demo_artifact_creation()
    design_id = demo_design_doc_creation(spec_id)
    code_id = demo_code_patch_creation(design_id)
    
    if not all([spec_id, design_id, code_id]):
        print("❌ Cannot demo handoff without artifacts")
        return
    
    print("\n--- Testing Valid Handoff: Project Manager -> Code Generator ---")
    result = handoff_protocol.validate_handoff(
        from_agent="project_manager",
        to_agent="code_generator", 
        artifacts=[spec_id]
    )
    print(f"Status: {result.status}")
    print(f"Valid artifacts: {len(result.validated_artifacts)}")
    if result.validation_errors:
        print(f"Errors: {result.validation_errors}")
    
    print("\n--- Testing Invalid Handoff: Test Writer -> UI Designer ---")
    result = handoff_protocol.validate_handoff(
        from_agent="test_writer",
        to_agent="ui_designer",
        artifacts=[code_id]  # Test writer giving code to UI designer - invalid flow
    )
    print(f"Status: {result.status}")
    print(f"Errors: {result.validation_errors}")
    print(f"Recommendations: {result.recommendations}")
    
    print("\n--- Agent Capabilities ---")
    capabilities = handoff_protocol.get_agent_capabilities("code_generator")
    print(f"Code Generator can produce: {capabilities['produces']}")
    print(f"Code Generator can consume: {capabilities['consumes']}")


def demo_conflict_detection():
    """Demonstrate conflict detection and resolution"""
    print("\n=== CONFLICT DETECTION & RESOLUTION DEMO ===")
    
    artifact_handler = TypedArtifactHandler()
    conflict_resolver = ConflictResolver(artifact_handler)
    
    # Create conflicting SpecDoc artifacts
    spec_data_1 = {
        "title": "E-commerce Platform Requirements v1",
        "objective": "Build a basic e-commerce platform with essential features",
        "scope": "Simple web application with basic shopping cart",
        "requirements": [
            {
                "id": "REQ-001",
                "description": "Users must be able to login with username and password",
                "priority": "high"
            }
        ],
        "acceptance_criteria": ["User login works", "Cart functionality present"]
    }
    
    spec_data_2 = {
        "title": "E-commerce Platform Requirements v2", 
        "objective": "Build a comprehensive e-commerce platform with advanced features",
        "scope": "Full-featured application with AI recommendations and social features",
        "requirements": [
            {
                "id": "REQ-001",
                "description": "Users must be able to login with Google, Facebook, or email",
                "priority": "high"
            }
        ],
        "acceptance_criteria": ["Social login works", "AI recommendations active"]
    }
    
    result1 = artifact_handler.create_artifact(spec_data_1, "SpecDoc", "project_manager")
    result2 = artifact_handler.create_artifact(spec_data_2, "SpecDoc", "project_manager")
    
    if "error" in result1 or "error" in result2:
        print("❌ Failed to create conflicting artifacts")
        return
    
    artifact_ids = [result1['artifact']['artifact_id'], result2['artifact']['artifact_id']]
    
    print("--- Detecting Conflicts ---")
    conflicts = conflict_resolver.detect_conflicts(artifact_ids)
    
    if conflicts:
        for conflict in conflicts:
            print(f"⚠️ Conflict detected: {conflict.conflict_type}")
            print(f"   Severity: {conflict.severity}")
            print(f"   Description: {conflict.description}")
            print(f"   Similarity Score: {conflict.similarity_score:.2f}")
    else:
        print("✅ No conflicts detected")
    
    if conflicts:
        print("\n--- Generating Resolution Options ---")
        options = conflict_resolver.get_resolution_options(conflicts)
        
        for i, option in enumerate(options):
            print(f"\nOption {i+1}: {option.strategy}")
            print(f"   Description: {option.description}")
            print(f"   Confidence: {option.confidence:.2f}")
            print(f"   Advantages: {', '.join(option.advantages)}")
        
        print("\n--- Applying Resolution ---")
        resolution = conflict_resolver.resolve_artifacts(artifact_ids)
        
        print(f"Resolution Status: {'✅ Success' if resolution.success else '❌ Failed'}")
        print(f"Strategy Used: {resolution.strategy_used}")
        print(f"Description: {resolution.resolution_description}")
        print(f"Quality Score: {resolution.resolution_quality:.2f}")


def demo_artifact_metrics():
    """Show comprehensive metrics about the artifact system"""
    print("\n=== ARTIFACT SYSTEM METRICS ===")
    
    artifact_handler = TypedArtifactHandler()
    handoff_protocol = AgentHandoff(artifact_handler)
    conflict_resolver = ConflictResolver(artifact_handler)
    
    # Get all artifacts
    artifacts = artifact_handler.list_artifacts()
    print(f"Total Artifacts Created: {len(artifacts)}")
    
    # Artifact type distribution
    type_counts = {}
    for artifact_data in artifacts:
        artifact_type = artifact_data['artifact']['artifact_type']
        type_counts[artifact_type] = type_counts.get(artifact_type, 0) + 1
    
    print("\nArtifact Type Distribution:")
    for artifact_type, count in type_counts.items():
        print(f"   {artifact_type}: {count}")
    
    # Handoff metrics
    handoff_metrics = handoff_protocol.get_handoff_metrics()
    print(f"\nHandoff Metrics:")
    print(f"   Total Handoffs: {handoff_metrics['total_handoffs']}")
    print(f"   Success Rate: {handoff_metrics.get('success_rate', 0):.1%}")
    
    # Conflict metrics
    conflict_metrics = conflict_resolver.get_conflict_metrics()
    print(f"\nConflict Resolution Metrics:")
    print(f"   Total Conflicts: {conflict_metrics['total_conflicts']}")
    print(f"   Resolution Rate: {conflict_metrics.get('resolution_rate', 0):.1%}")
    
    if conflict_metrics.get('conflict_types'):
        print("\nConflict Type Distribution:")
        for conflict_type, count in conflict_metrics['conflict_types'].items():
            print(f"   {conflict_type}: {count}")


def main():
    """Run the complete typed artifact system demonstration"""
    print("🚀 TYPED ARTIFACT SYSTEM DEMONSTRATION")
    print("=" * 50)
    
    try:
        # Create sample artifacts
        spec_id = demo_artifact_creation()
        if spec_id:
            design_id = demo_design_doc_creation(spec_id)
            if design_id:
                code_id = demo_code_patch_creation(design_id)
        
        # Demonstrate handoff validation
        demo_handoff_validation()
        
        # Demonstrate conflict detection
        demo_conflict_detection()
        
        # Show system metrics
        demo_artifact_metrics()
        
        print("\n" + "=" * 50)
        print("✅ DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("\nKey Features Demonstrated:")
        print("   ✓ Strict artifact schema validation")
        print("   ✓ Confidence scoring and quality metrics")
        print("   ✓ Agent handoff protocol enforcement")
        print("   ✓ Conflict detection and resolution")
        print("   ✓ Lineage tracking and versioning")
        print("   ✓ Comprehensive system metrics")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ DEMONSTRATION FAILED: {e}")


if __name__ == "__main__":
    main()