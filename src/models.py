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
    protocol: str
    urgency: int
    ambulance_report: str
    eta_minutes: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
