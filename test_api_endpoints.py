"""
Test script for the new FastAPI endpoints:
- GET /health
- POST /simulate_task
"""

import json
import requests
import asyncio
from typing import Dict, Any

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🏥 Testing GET /health endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Health check successful")
            print(f"    ok: {data.get('ok')}")
            print(f"    event_bus: {data.get('event_bus')}")
            print(f"    redis_ok: {data.get('redis_ok')}")
            print(f"    db_ok: {data.get('db_ok')}")
            return data
        else:
            print(f"  ❌ Health check failed: {response.status_code}")
            print(f"    Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("  ⚠️  Could not connect to API server (not running on port 8000)")
        return None
    except Exception as e:
        print(f"  ❌ Error testing health endpoint: {e}")
        return None

def test_simulate_task_endpoint():
    """Test the simulate task endpoint"""
    print("\n📋 Testing POST /simulate_task endpoint...")
    
    try:
        payload = {
            "objective": "Create a sample web application with user authentication"
        }
        
        response = requests.post(
            "http://localhost:8000/simulate_task", 
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Task simulation successful")
            print(f"    task_id: {data.get('task_id')}")
            return data
        else:
            print(f"  ❌ Task simulation failed: {response.status_code}")
            print(f"    Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("  ⚠️  Could not connect to API server (not running on port 8000)")
        return None
    except Exception as e:
        print(f"  ❌ Error testing simulate_task endpoint: {e}")
        return None

def test_endpoints_with_curl():
    """Show equivalent curl commands for testing"""
    print("\n🌐 Equivalent curl commands for manual testing:")
    print("\n1. Health Check:")
    print("   curl -X GET http://localhost:8000/health")
    print("\n2. Simulate Task:")
    print('   curl -X POST http://localhost:8000/simulate_task \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"objective": "Create a sample web application"}\'')

if __name__ == "__main__":
    print("🧪 API Endpoints Test Suite")
    print("=" * 50)
    
    # Test health endpoint
    health_result = test_health_endpoint()
    
    # Test simulate task endpoint
    task_result = test_simulate_task_endpoint()
    
    # Show curl examples
    test_endpoints_with_curl()
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"  Health endpoint: {'✅ Working' if health_result else '❌ Failed'}")
    print(f"  Simulate task endpoint: {'✅ Working' if task_result else '❌ Failed'}")
    
    if not health_result and not task_result:
        print(f"\n💡 To test the endpoints, start the API server:")
        print(f"   python api_server.py")
        print(f"   # Or with uvicorn:")
        print(f"   uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload")