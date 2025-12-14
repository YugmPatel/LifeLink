"""
API Models for EDFlow AI
Pydantic models for request/response serialization
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

# Enums
class CaseType(str, Enum):
    STEMI = "STEMI"
    STROKE = "Stroke"
    TRAUMA = "Trauma"
    GENERAL = "General"
    PEDIATRIC = "Pediatric"

class CaseStatus(str, Enum):
    ARRIVING = "Arriving"
    TRIAGED = "Triaged"
    IN_TREATMENT = "In Treatment"
    PENDING = "Pending"
    ADMITTED = "Admitted"
    DISCHARGED = "Discharged"

class ActivityType(str, Enum):
    LAB = "Lab"
    PHARM = "Pharm"
    BED = "Bed"
    DOCTOR = "Doctor"
    SYSTEM = "System"
    AGENT = "Agent"

class ActivityStatus(str, Enum):
    READY = "Ready"
    PENDING = "Pending"
    COMPLETE = "Complete"
    FAILED = "Failed"
    IN_PROGRESS = "In Progress"

class MessageType(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

class AgentType(str, Enum):
    ED_COORDINATOR = "ed_coordinator"
    RESOURCE_MANAGER = "resource_manager"
    SPECIALIST_COORDINATOR = "specialist_coordinator"
    LAB_SERVICE = "lab_service"
    PHARMACY = "pharmacy"
    BED_MANAGEMENT = "bed_management"
    WHATSAPP_NOTIFICATION = "whatsapp_notification"

# Core Models
class PatientVitals(BaseModel):
    hr: int = Field(..., description="Heart rate (bpm)", ge=0, le=300)
    bp_sys: int = Field(..., description="Systolic blood pressure (mmHg)", ge=0, le=300)
    bp_dia: int = Field(..., description="Diastolic blood pressure (mmHg)", ge=0, le=200)
    spo2: int = Field(..., description="Oxygen saturation (%)", ge=0, le=100)
    temp: Optional[float] = Field(None, description="Temperature (°C)", ge=30.0, le=45.0)

class PatientCase(BaseModel):
    id: str = Field(..., description="Unique case identifier")
    type: CaseType = Field(..., description="Case type")
    duration: int = Field(..., description="Minutes since arrival", ge=0)
    vitals: PatientVitals = Field(..., description="Patient vital signs")
    status: CaseStatus = Field(..., description="Current case status")
    location: str = Field(..., description="Current location in ED")
    lab_eta: Optional[int] = Field(None, description="Lab ETA in minutes", ge=0)
    assigned_bed: Optional[str] = Field(None, description="Assigned bed identifier")
    priority: int = Field(..., description="Priority level (1=critical, 5=minimal)", ge=1, le=5)
    timestamp: datetime = Field(..., description="Case creation timestamp")
    chief_complaint: Optional[str] = Field(None, description="Chief complaint")
    ems_report: Optional[str] = Field(None, description="EMS report")

class DashboardMetrics(BaseModel):
    active_cases: int = Field(..., description="Number of active cases", ge=0)
    avg_lab_eta: int = Field(..., description="Average lab ETA in minutes", ge=0)
    icu_beds_held: int = Field(..., description="Number of ICU beds held", ge=0)
    doctors_paged: int = Field(..., description="Number of doctors paged", ge=0)
    last_updated: datetime = Field(..., description="Last update timestamp")

class ActivityEntry(BaseModel):
    id: str = Field(..., description="Unique activity identifier")
    timestamp: datetime = Field(..., description="Activity timestamp")
    type: ActivityType = Field(..., description="Activity type")
    message: str = Field(..., description="Activity message")
    status: ActivityStatus = Field(..., description="Activity status")
    case_id: Optional[str] = Field(None, description="Related case ID")
    agent_name: Optional[str] = Field(None, description="Agent name")
    priority: Optional[str] = Field(None, description="Priority level")

class ChatMessage(BaseModel):
    id: str = Field(..., description="Unique message identifier")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    sender: str = Field(..., description="Message sender")
    type: MessageType = Field(..., description="Message type")
    agent_type: Optional[AgentType] = Field(None, description="Agent type if applicable")

class AgentStatus(BaseModel):
    name: str = Field(..., description="Agent name")
    type: AgentType = Field(..., description="Agent type")
    status: str = Field(..., description="Agent status (online/offline/busy)")
    last_seen: datetime = Field(..., description="Last seen timestamp")
    address: str = Field(..., description="Agent address")
    message_count: int = Field(..., description="Message count", ge=0)

# Request Models
class SimulationRequest(BaseModel):
    case_type: CaseType = Field(..., description="Type of case to simulate")
    patient_data: Optional[Dict[str, Any]] = Field(None, description="Optional patient data")

class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="Message content", min_length=1, max_length=1000)
    sender: str = Field(..., description="Message sender", min_length=1, max_length=100)

# Response Models
class SimulationResponse(BaseModel):
    message: str = Field(..., description="Response message")
    patient_id: str = Field(..., description="Generated patient ID")
    case_type: CaseType = Field(..., description="Case type")
    timestamp: datetime = Field(..., description="Simulation timestamp")
    success: bool = Field(..., description="Success status")

class ApiResponse(BaseModel):
    success: bool = Field(..., description="Success status")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    data: Optional[Any] = Field(None, description="Response data")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# WebSocket Event Models
class WebSocketEvent(BaseModel):
    type: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")

class PatientArrivalEvent(WebSocketEvent):
    type: str = Field(default="patient_arrival", description="Event type")
    data: Dict[str, Any] = Field(..., description="Patient arrival data")

class ProtocolActivationEvent(WebSocketEvent):
    type: str = Field(default="protocol_activation", description="Event type")
    data: Dict[str, Any] = Field(..., description="Protocol activation data")

class CaseUpdateEvent(WebSocketEvent):
    type: str = Field(default="case_update", description="Event type")
    data: Dict[str, Any] = Field(..., description="Case update data")

class AgentMessageEvent(WebSocketEvent):
    type: str = Field(default="agent_message", description="Event type")
    data: Dict[str, Any] = Field(..., description="Agent message data")

# Health Check Models
class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    agents_active: int = Field(..., description="Number of active agents", ge=0)
    version: str = Field(..., description="API version")
    uptime: Optional[float] = Field(None, description="Uptime in seconds")

# Configuration Models
class ApiConfig(BaseModel):
    cors_origins: List[str] = Field(default=["http://localhost:3000"], description="CORS origins")
    websocket_origins: List[str] = Field(default=["http://localhost:3000"], description="WebSocket origins")
    max_connections: int = Field(default=100, description="Max WebSocket connections", ge=1)
    heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds", ge=1)

# Utility Models
class PaginationParams(BaseModel):
    page: int = Field(default=1, description="Page number", ge=1)
    limit: int = Field(default=20, description="Items per page", ge=1, le=100)
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field(default="desc", description="Sort order (asc/desc)")

class FilterParams(BaseModel):
    case_type: Optional[CaseType] = Field(None, description="Filter by case type")
    status: Optional[CaseStatus] = Field(None, description="Filter by status")
    priority: Optional[int] = Field(None, description="Filter by priority", ge=1, le=5)
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")

# Export all models
__all__ = [
    # Enums
    "CaseType", "CaseStatus", "ActivityType", "ActivityStatus", "MessageType", "AgentType",
    # Core Models
    "PatientVitals", "PatientCase", "DashboardMetrics", "ActivityEntry", "ChatMessage", "AgentStatus",
    # Request Models
    "SimulationRequest", "ChatMessageRequest",
    # Response Models
    "SimulationResponse", "ApiResponse", "ErrorResponse",
    # WebSocket Models
    "WebSocketEvent", "PatientArrivalEvent", "ProtocolActivationEvent", "CaseUpdateEvent", "AgentMessageEvent",
    # Health Check
    "HealthCheckResponse",
    # Configuration
    "ApiConfig",
    # Utility
    "PaginationParams", "FilterParams"
]