"""
Demo showing how to integrate the vector memory system with the existing 
multi-agent project structure.
"""

import os
import logging
from memory.integration import VectorMemoryIntegration

# Setup logging
logging.basicConfig(level=logging.INFO)

def demo_system_integration():
    """Demonstrate integration with the existing agent system"""
    
    print("🔧 Vector Memory System Integration Demo")
    print("=" * 60)
    
    # Initialize the integration
    integration = VectorMemoryIntegration("memory/system_integration.db")
    
    # Simulate agent interactions being stored
    print("\n📝 Storing Agent Interactions...")
    
    # Store some sample agent responses
    agent_interactions = [
        {
            "agent": "ProjectManager", 
            "content": "I've analyzed your requirements for a web application. We'll need to create a React frontend with a Python FastAPI backend, including user authentication and a PostgreSQL database.",
            "type": "project_planning",
            "metadata": {"project_type": "web_app", "complexity": "medium"}
        },
        {
            "agent": "CodeGenerator",
            "content": "Here's the Python FastAPI server implementation with authentication endpoints, database models using SQLAlchemy, and CORS configuration for the frontend.",
            "type": "code_generation", 
            "metadata": {"language": "python", "framework": "fastapi"}
        },
        {
            "agent": "UIDesigner",
            "content": "I've created a modern React dashboard with responsive design, using Material-UI components and a clean color scheme. The layout includes navigation, data tables, and modal forms.",
            "type": "ui_design",
            "metadata": {"framework": "react", "ui_library": "material-ui"}
        },
        {
            "agent": "TestWriter",
            "content": "I've written comprehensive test suites including unit tests for API endpoints, integration tests for database operations, and end-to-end tests for the user authentication flow.",
            "type": "testing",
            "metadata": {"test_types": ["unit", "integration", "e2e"]}
        }
    ]
    
    handles = []
    for interaction in agent_interactions:
        handle = integration.store_agent_interaction(
            agent_name=interaction["agent"],
            interaction_content=interaction["content"],
            interaction_type=interaction["type"],
            metadata=interaction["metadata"]
        )
        handles.append(handle)
        print(f"  ✅ Stored {interaction['agent']} interaction -> {handle}")
    
    # Store some project artifacts
    print(f"\n📦 Storing Project Artifacts...")
    
    artifacts = [
        {
            "type": "code",
            "title": "User Authentication API", 
            "content": "from fastapi import FastAPI, Depends, HTTPException\nfrom fastapi.security import HTTPBearer\nimport jwt\n\napp = FastAPI()\nsecurity = HTTPBearer()\n\n@app.post('/auth/login')\nasync def login(credentials: UserCredentials):\n    # Authentication logic here\n    return {'token': generate_jwt_token(user)}"
        },
        {
            "type": "documentation",
            "title": "API Documentation",
            "content": "# User Authentication API\n\nThis API provides secure user authentication using JWT tokens.\n\n## Endpoints\n\n- POST /auth/login - User login\n- POST /auth/register - User registration\n- GET /auth/profile - Get user profile\n\n## Authentication\n\nAll protected endpoints require a Bearer token in the Authorization header."
        }
    ]
    
    for artifact in artifacts:
        handle = integration.store_project_artifact(
            artifact_type=artifact["type"],
            content=artifact["content"], 
            title=artifact["title"]
        )
        print(f"  ✅ Stored {artifact['type']} artifact: {artifact['title']} -> {handle}")
    
    # Demonstrate semantic search
    print(f"\n🔍 Semantic Search Examples...")
    
    search_scenarios = [
        {
            "query": "authentication and security implementation",
            "context": "CodeGenerator needs context about authentication"
        },
        {
            "query": "user interface design and components",
            "context": "UIDesigner needs styling guidance" 
        },
        {
            "query": "testing strategies and frameworks",
            "context": "TestWriter needs testing approach"
        },
        {
            "query": "database design and API structure", 
            "context": "ProjectManager needs architecture review"
        }
    ]
    
    for scenario in search_scenarios:
        print(f"\nScenario: {scenario['context']}")
        print(f"Query: '{scenario['query']}'")
        
        # Find similar interactions
        interactions = integration.find_similar_interactions(scenario['query'], top_k=2)
        if interactions:
            print("  Similar Interactions:")
            for result in interactions:
                metadata = result['metadata']
                print(f"    • {metadata.get('agent_name', 'Unknown')} ({result['similarity_score']:.3f}) - {metadata.get('interaction_type', 'N/A')}")
        
        # Find similar artifacts  
        artifacts = integration.find_similar_artifacts(scenario['query'], top_k=2)
        if artifacts:
            print("  Similar Artifacts:")
            for result in artifacts:
                metadata = result['metadata']
                print(f"    • {metadata.get('title', 'Untitled')} ({result['similarity_score']:.3f}) - {metadata.get('artifact_type', 'N/A')}")
    
    # Demonstrate context handle system
    print(f"\n🔗 Context Handle System...")
    
    context_queries = [
        "web application architecture",
        "React component design", 
        "API testing methodology"
    ]
    
    for query in context_queries:
        print(f"\nQuery: '{query}'")
        context_handles = integration.get_context_for_agent("DemoAgent", query, max_contexts=3)
        
        if context_handles:
            print(f"  Context handles provided: {len(context_handles)}")
            for i, handle in enumerate(context_handles, 1):
                print(f"    {i}. {handle}")
                
                # Show how to expand handle to get full content
                expanded = integration.expand_context_handle(handle)
                if expanded:
                    content_preview = expanded['text_content'][:80] + "..." if len(expanded['text_content']) > 80 else expanded['text_content']
                    print(f"       Content: {content_preview}")
        else:
            print("  No relevant context found")
    
    # Show memory statistics
    print(f"\n📊 Vector Memory Statistics:")
    stats = integration.get_memory_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n✅ System integration demo completed!")
    print(f"\nKey Benefits:")
    print("  • Semantic search across agent interactions and artifacts")
    print("  • Context handles prevent memory bloat")
    print("  • Fallback to TF-IDF when OpenAI unavailable") 
    print("  • Integrated with existing project memory system")
    print("  • Supports metadata filtering and importance scoring")
    
    return integration

if __name__ == "__main__":
    demo_system_integration()