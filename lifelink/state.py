"""
LifeLink shared state type definitions.

This module defines the TypedDict used as shared state across all LangGraph nodes.
"""

from typing import TypedDict, Optional
from typing_extensions import Annotated
import operator


class LifeLinkState(TypedDict):
    """
    Shared state for the LifeLink LangGraph pipeline.
    
    Attributes:
        raw_ambulance_report: The incoming ambulance report text
        ai_analysis: Claude AI analysis results (protocol, urgency, analysis)
        hospital_data: Current hospital status from JSONBin
        protocol_name: Activated protocol (STEMI, Stroke, Trauma, General)
        agent_reports: Dictionary of reports from each agent node
        whatsapp_result: Result of WhatsApp notification
        errors: List of errors encountered during execution
        final_response: Aggregated final coordination report
    """
    # Input
    raw_ambulance_report: str
    
    # Coordinator outputs
    ai_analysis: Optional[dict]
    hospital_data: Optional[dict]
    protocol_name: Optional[str]  # "STEMI", "Stroke", "Trauma", "General"
    
    # Agent reports (accumulated via reducer)
    agent_reports: Annotated[dict[str, str], operator.or_]
    
    # WhatsApp result
    whatsapp_result: Optional[str]
    
    # Error tracking
    errors: Annotated[list[str], operator.add]
    
    # Final output
    final_response: Optional[str]
