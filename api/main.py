"""
LifeLink API - Instant Emergency, Instant Response
Main application that bridges LangGraph agents with React frontend
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import socketio
import uvicorn

from .routes import dashboard, cases, agents, simulation
from .websocket.manager import WebSocketManager
from .models.api_models import *
from lifelink import run_lifelink_case
from src.utils import get_config, get_logger

# Setup logging
logger = get_logger(__name__)
config = get_config()

# Global variables
ws_manager = None
# In-memory storage for active patients
active_patients: Dict[str, dict] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global ws_manager
    
    logger.info("🚀 Starting LifeLink API Server...")
    
    try:
        logger.info("✅ LifeLink LangGraph pipeline ready")
        api_port = getattr(config, 'API_PORT', 8080)
        logger.info(f"🏥 LifeLink API Server ready on port {api_port}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize LifeLink: {str(e)}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down LifeLink API Server...")

# Create FastAPI app
app = FastAPI(
    title="LifeLink API",
    description="LifeLink - Instant Emergency, Instant Response",
    version="1.0.0",
    lifespan=lifespan
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    logger=True,
    engineio_logger=True
)

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Initialize WebSocket manager
ws_manager = WebSocketManager(sio)

# Include API routes
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(cases.router, prefix="/api/cases", tags=["cases"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "pipeline": "LangGraph",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "LifeLink - Instant Emergency, Instant Response",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "pipeline": "LangGraph"
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Utility functions to access shared state from routes
def get_active_patients() -> Dict[str, dict]:
    """Get active patients dictionary"""
    return active_patients

def get_websocket_manager():
    """Get WebSocket manager"""
    if not ws_manager:
        raise HTTPException(status_code=503, detail="WebSocket manager not available")
    return ws_manager

async def process_ambulance_case(ambulance_text: str) -> dict:
    """
    Process an ambulance case through the LangGraph pipeline.
    
    Args:
        ambulance_text: The ambulance report text
        
    Returns:
        dict with pipeline results
    """
    return await run_lifelink_case(ambulance_text)

if __name__ == "__main__":
    # Run the server
    port = getattr(config, 'API_PORT', 8080)
    uvicorn.run(
        "api.main:socket_app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
