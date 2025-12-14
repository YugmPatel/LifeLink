"""
LifeLink LangGraph builder and entry functions.

This module provides the graph construction and main entry point for running
the LifeLink emergency coordination pipeline.
"""

from typing import Any
from langgraph.graph import StateGraph, START, END

from lifelink.state import LifeLinkState


def build_lifelink_graph() -> StateGraph:
    """
    Build and return the configured LangGraph StateGraph.
    
    Graph topology:
    - START -> coordinator_node
    - coordinator_node -> [parallel branch to all agent nodes]
    - All agent nodes -> aggregate_node
    - aggregate_node -> END
    
    Returns:
        Configured StateGraph ready for compilation
    """
    # Import nodes here to avoid circular imports
    from lifelink.nodes import (
        coordinator_node,
        resource_manager_node,
        specialist_coordinator_node,
        lab_service_node,
        pharmacy_node,
        bed_management_node,
        whatsapp_notification_node,
        aggregate_node,
    )
    
    # Create the graph with LifeLinkState
    graph = StateGraph(LifeLinkState)
    
    # Add all nodes
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("resource_manager", resource_manager_node)
    graph.add_node("specialist_coordinator", specialist_coordinator_node)
    graph.add_node("lab_service", lab_service_node)
    graph.add_node("pharmacy", pharmacy_node)
    graph.add_node("bed_management", bed_management_node)
    graph.add_node("whatsapp_notification", whatsapp_notification_node)
    graph.add_node("aggregate", aggregate_node)
    
    # Define edges: START -> coordinator
    graph.add_edge(START, "coordinator")
    
    # Coordinator -> parallel agent nodes
    graph.add_edge("coordinator", "resource_manager")
    graph.add_edge("coordinator", "specialist_coordinator")
    graph.add_edge("coordinator", "lab_service")
    graph.add_edge("coordinator", "pharmacy")
    graph.add_edge("coordinator", "bed_management")
    graph.add_edge("coordinator", "whatsapp_notification")
    
    # All agent nodes -> aggregate
    graph.add_edge("resource_manager", "aggregate")
    graph.add_edge("specialist_coordinator", "aggregate")
    graph.add_edge("lab_service", "aggregate")
    graph.add_edge("pharmacy", "aggregate")
    graph.add_edge("bed_management", "aggregate")
    graph.add_edge("whatsapp_notification", "aggregate")
    
    # Aggregate -> END
    graph.add_edge("aggregate", END)
    
    return graph


async def run_lifelink_case(ambulance_text: str) -> dict[str, Any]:
    """
    Main entry point for running the LifeLink pipeline.
    
    Args:
        ambulance_text: The ambulance report text
        
    Returns:
        dict with keys:
        - final_response: str - Aggregated coordination report
        - ai_analysis: dict - Claude AI analysis results
        - agent_reports: dict - Individual agent reports
        - protocol_name: str - Activated protocol
        - errors: list - Any errors encountered
    """
    try:
        # Build and compile the graph
        graph = build_lifelink_graph()
        compiled = graph.compile()
        
        # Initialize state with the ambulance report
        initial_state: LifeLinkState = {
            "raw_ambulance_report": ambulance_text,
            "ai_analysis": None,
            "hospital_data": None,
            "protocol_name": None,
            "agent_reports": {},
            "whatsapp_result": None,
            "errors": [],
            "final_response": None,
        }
        
        # Execute the graph
        final_state = await compiled.ainvoke(initial_state)
        
        # Return the result
        return {
            "final_response": final_state.get("final_response", ""),
            "ai_analysis": final_state.get("ai_analysis"),
            "agent_reports": final_state.get("agent_reports", {}),
            "protocol_name": final_state.get("protocol_name"),
            "whatsapp_result": final_state.get("whatsapp_result"),
            "errors": final_state.get("errors", []),
        }
        
    except Exception as e:
        # Return partial results with error information
        return {
            "final_response": f"Error during pipeline execution: {str(e)}",
            "ai_analysis": None,
            "agent_reports": {},
            "protocol_name": None,
            "errors": [f"Pipeline error: {str(e)}"],
        }
