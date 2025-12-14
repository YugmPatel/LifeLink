"""
Agents API Routes
Endpoints for agent status, communication, and management.
Updated for LangGraph architecture - agents are now nodes in the graph.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ..models.api_models import (
    AgentStatus, ChatMessage, ApiResponse, AgentType
)
from src.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()

# LangGraph node names that correspond to agents
LANGGRAPH_AGENTS = {
    "ed_coordinator": {
        "name": "ED Coordinator",
        "type": AgentType.ED_COORDINATOR,
        "description": "Central orchestrator for ED operations (LangGraph coordinator node)"
    },
    "resource_manager": {
        "name": "Resource Manager",
        "type": AgentType.RESOURCE_MANAGER,
        "description": "Manages beds, equipment, and resources (LangGraph node)"
    },
    "specialist_coordinator": {
        "name": "Specialist Coordinator",
        "type": AgentType.SPECIALIST_COORDINATOR,
        "description": "Coordinates specialist teams and doctors (LangGraph node)"
    },
    "lab_service": {
        "name": "Lab Service",
        "type": AgentType.LAB_SERVICE,
        "description": "Manages laboratory tests and results (LangGraph node)"
    },
    "pharmacy": {
        "name": "Pharmacy",
        "type": AgentType.PHARMACY,
        "description": "Handles medication orders and delivery (LangGraph node)"
    },
    "bed_management": {
        "name": "Bed Management",
        "type": AgentType.BED_MANAGEMENT,
        "description": "Manages bed assignments and turnover (LangGraph node)"
    }
}

def get_websocket_manager():
    from api.main import get_websocket_manager
    return get_websocket_manager()


@router.get("/status", response_model=List[AgentStatus])
async def get_agents_status():
    """
    Get status of all LangGraph agent nodes
    
    Returns:
        List[AgentStatus]: Status of all 6 agent nodes
    """
    try:
        agent_statuses = []
        
        # All LangGraph nodes are always "online" as they're part of the graph
        for agent_key, info in LANGGRAPH_AGENTS.items():
            agent_status = AgentStatus(
                name=info["name"],
                type=info["type"],
                status="online",
                last_seen=datetime.utcnow(),
                address=f"langgraph://{agent_key}_node",
                message_count=0
            )
            agent_statuses.append(agent_status)
        
        logger.info(f"Retrieved status for {len(agent_statuses)} LangGraph agent nodes")
        return agent_statuses
        
    except Exception as e:
        logger.error(f"Error retrieving agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent status: {str(e)}")


@router.get("/messages", response_model=List[ChatMessage])
async def get_agent_messages(
    agent_type: Optional[AgentType] = Query(None, description="Filter by agent type"),
    limit: int = Query(50, description="Maximum number of messages", ge=1, le=100)
):
    """
    Get recent agent messages
    
    Args:
        agent_type: Optional filter by agent type
        limit: Maximum number of messages to return
        
    Returns:
        List[ChatMessage]: Recent agent messages
    """
    try:
        ws_manager = get_websocket_manager()
        
        # Get message history from WebSocket manager
        messages = ws_manager.get_message_history(limit)
        
        # Convert to ChatMessage objects
        chat_messages = []
        for msg_data in messages:
            try:
                chat_message = ChatMessage(
                    id=msg_data['id'],
                    content=msg_data['content'],
                    timestamp=datetime.fromisoformat(msg_data['timestamp'].replace('Z', '+00:00')),
                    sender=msg_data['sender'],
                    type=msg_data['type'],
                    agent_type=msg_data.get('agent_type')
                )
                chat_messages.append(chat_message)
            except Exception as e:
                logger.warning(f"Error parsing message: {str(e)}")
                continue
        
        # Filter by agent type if specified
        if agent_type:
            chat_messages = [msg for msg in chat_messages if msg.agent_type == agent_type]
        
        logger.info(f"Retrieved {len(chat_messages)} agent messages")
        return chat_messages
        
    except Exception as e:
        logger.error(f"Error retrieving agent messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")


@router.get("/health", response_model=ApiResponse)
async def get_agents_health():
    """
    Get overall LangGraph agent system health
    
    Returns:
        ApiResponse: Agent system health information
    """
    try:
        # All LangGraph nodes are always available
        online_agents = len(LANGGRAPH_AGENTS)
        total_agents = len(LANGGRAPH_AGENTS)
        health_percentage = 100.0
        overall_status = "healthy"
        
        health_data = {
            "overall_status": overall_status,
            "health_percentage": health_percentage,
            "agents_online": online_agents,
            "agents_total": total_agents,
            "agents_offline": 0,
            "last_check": datetime.utcnow().isoformat(),
            "system_uptime": "operational",
            "pipeline": "LangGraph"
        }
        
        return ApiResponse(
            success=True,
            message=f"LangGraph agent system health: {overall_status}",
            data=health_data
        )
        
    except Exception as e:
        logger.error(f"Error checking agent health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check agent health: {str(e)}")


@router.get("/{agent_type}/status", response_model=AgentStatus)
async def get_specific_agent_status(agent_type: AgentType):
    """
    Get status of a specific LangGraph agent node
    
    Args:
        agent_type: The type of agent to get status for
        
    Returns:
        AgentStatus: Status of the specified agent node
    """
    try:
        # Map agent types to keys
        agent_key_map = {
            AgentType.ED_COORDINATOR: "ed_coordinator",
            AgentType.RESOURCE_MANAGER: "resource_manager",
            AgentType.SPECIALIST_COORDINATOR: "specialist_coordinator",
            AgentType.LAB_SERVICE: "lab_service",
            AgentType.PHARMACY: "pharmacy",
            AgentType.BED_MANAGEMENT: "bed_management"
        }
        
        agent_key = agent_key_map.get(agent_type)
        if not agent_key or agent_key not in LANGGRAPH_AGENTS:
            raise HTTPException(status_code=404, detail=f"Agent type {agent_type} not found")
        
        info = LANGGRAPH_AGENTS[agent_key]
        
        agent_status = AgentStatus(
            name=info["name"],
            type=info["type"],
            status="online",
            last_seen=datetime.utcnow(),
            address=f"langgraph://{agent_key}_node",
            message_count=0
        )
        
        logger.info(f"Retrieved status for {agent_type} LangGraph node: online")
        return agent_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving {agent_type} agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve {agent_type} status: {str(e)}")


@router.post("/{agent_type}/restart", response_model=ApiResponse)
async def restart_agent(agent_type: AgentType):
    """
    Restart a specific agent (no-op for LangGraph - nodes don't need restart)
    
    Args:
        agent_type: The type of agent to restart
        
    Returns:
        ApiResponse: Restart operation result
    """
    try:
        agent_key_map = {
            AgentType.ED_COORDINATOR: "ed_coordinator",
            AgentType.RESOURCE_MANAGER: "resource_manager",
            AgentType.SPECIALIST_COORDINATOR: "specialist_coordinator",
            AgentType.LAB_SERVICE: "lab_service",
            AgentType.PHARMACY: "pharmacy",
            AgentType.BED_MANAGEMENT: "bed_management"
        }
        
        agent_key = agent_key_map.get(agent_type)
        if not agent_key or agent_key not in LANGGRAPH_AGENTS:
            raise HTTPException(status_code=404, detail=f"Agent type {agent_type} not found")
        
        info = LANGGRAPH_AGENTS[agent_key]
        
        logger.info(f"Restart requested for {agent_type} LangGraph node (no-op)")
        
        return ApiResponse(
            success=True,
            message=f"{info['name']} LangGraph node is always available (restart not needed)",
            data={
                "agent_type": agent_type,
                "agent_name": info["name"],
                "restart_time": datetime.utcnow().isoformat(),
                "status": "online",
                "pipeline": "LangGraph",
                "note": "LangGraph nodes are stateless and always available"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error with restart request for {agent_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process restart for {agent_type}: {str(e)}")


@router.post("/chat", response_model=ApiResponse)
async def send_chat_message(
    message: dict
):
    """
    Send a chat message to the LangGraph pipeline for processing.
    
    Args:
        message: Dict with "content" key containing the message text
        
    Returns:
        ApiResponse: LangGraph pipeline response
    """
    try:
        from api.main import process_ambulance_case
        
        content = message.get("content", "")
        if not content:
            raise HTTPException(status_code=400, detail="Message content is required")
        
        logger.info(f"Processing chat message through LangGraph: {content[:50]}...")
        
        # Run through LangGraph pipeline
        result = await process_ambulance_case(content)
        
        protocol = result.get("protocol_name", "General")
        final_response = result.get("final_response", "Message processed.")
        
        return ApiResponse(
            success=True,
            message="Message processed by LangGraph pipeline",
            data={
                "protocol": protocol,
                "response": final_response,
                "ai_analysis": result.get("ai_analysis"),
                "agent_reports": result.get("agent_reports", {}),
                "errors": result.get("errors", [])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/communication/stats", response_model=ApiResponse)
async def get_communication_stats():
    """
    Get agent communication statistics
    
    Returns:
        ApiResponse: Communication statistics
    """
    try:
        ws_manager = get_websocket_manager()
        
        # Get basic stats
        connected_clients = ws_manager.get_connected_clients_count()
        message_history = ws_manager.get_message_history(100)
        
        # Calculate message stats
        total_messages = len(message_history)
        agent_messages = len([msg for msg in message_history if msg.get('type') == 'agent'])
        user_messages = len([msg for msg in message_history if msg.get('type') == 'user'])
        
        stats_data = {
            "connected_clients": connected_clients,
            "total_messages": total_messages,
            "agent_messages": agent_messages,
            "user_messages": user_messages,
            "active_agents": len(LANGGRAPH_AGENTS),
            "last_message_time": message_history[-1].get('timestamp') if message_history else None,
            "communication_status": "active" if connected_clients > 0 else "idle",
            "pipeline": "LangGraph"
        }
        
        return ApiResponse(
            success=True,
            message="Communication statistics retrieved successfully",
            data=stats_data
        )
        
    except Exception as e:
        logger.error(f"Error retrieving communication stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve communication stats: {str(e)}")
