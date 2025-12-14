#!/usr/bin/env python3
"""
LifeLink API Server Startup Script
Runs the FastAPI server with WebSocket support
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "EDFlow AI"))

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = f"{current_dir}:{current_dir / 'EDFlow AI'}"

def main():
    """Main entry point for API server"""
    
    print("🏥 EDFlow AI - API Server")
    print("=" * 50)
    print("Starting FastAPI server with WebSocket support...")
    print("Frontend: http://localhost:3000")
    print("API Docs: http://localhost:8080/docs")
    print("Health Check: http://localhost:8080/health")
    print("=" * 50)
    
    # Set environment variables if not set
    os.environ.setdefault("DEPLOYMENT_MODE", "local")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("API_PORT", "8080")
    
    # Import after setting up paths
    try:
        from api.main import socket_app
        
        # Run the server
        uvicorn.run(
            "api.main:socket_app",
            host="0.0.0.0",
            port=8080,
            reload=False,  # Disable reload for now to avoid import issues
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you have installed the required dependencies:")
        print("pip install -r EDFlow AI/requirements.txt")
        print("pip install -r api_requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()