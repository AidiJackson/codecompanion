"""
Quick script to start the FastAPI server with the new endpoints.
"""

import uvicorn
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Starting FastAPI server with new endpoints:")
    print("   GET  /health - Health check with event bus and database status")
    print("   POST /simulate_task - Simulate task creation for development")
    print("\nServer will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )