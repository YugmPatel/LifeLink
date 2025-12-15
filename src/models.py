"""
LifeLink Data Models
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class PatientArrivalNotification(BaseModel):
    """Patient arrival notification model"""
    patient_id: str
    arrival_time: datetime
    vitals: Dict[str, Any] = {}
    chief_complaint: str = ""
    ems_report: str = ""
    priority: int = 2
    demographics: Optional[Dict[str, Any]] = None
    # Optional fields for backward compatibility
    protocol: Optional[str] = None
    urgency: Optional[int] = None
    ambulance_report: Optional[str] = None
    eta_minutes: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
