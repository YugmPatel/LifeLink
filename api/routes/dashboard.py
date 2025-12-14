"""
Dashboard API Routes
Endpoints for dashboard metrics, cases, and activity data
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from ..models.api_models import (
    DashboardMetrics, PatientCase, ActivityEntry, ApiResponse,
    FilterParams, PaginationParams
)
from src.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()

# In-memory storage for dashboard data (shared with main.py)
_active_cases = {}
_recent_activities = []


def get_active_patients():
    """Get active patients from main module"""
    from api.main import get_active_patients
    return get_active_patients()


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """
    Get current ED dashboard metrics
    
    Returns:
        DashboardMetrics: Current metrics including active cases, lab ETA, etc.
    """
    try:
        active_patients = get_active_patients()
        
        metrics = DashboardMetrics(
            active_cases=len(active_patients),
            avg_lab_eta=9,
            icu_beds_held=2,
            doctors_paged=2,
            last_updated=datetime.utcnow()
        )
        
        logger.info(f"Dashboard metrics retrieved: {len(active_patients)} active cases")
        return metrics
        
    except Exception as e:
        logger.error(f"Error retrieving dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/cases", response_model=List[PatientCase])
async def get_active_cases(
    filters: FilterParams = Depends(),
    pagination: PaginationParams = Depends()
):
    """
    Get all active patient cases
    """
    try:
        active_patients = get_active_patients()
        
        cases = []
        for patient_id, patient_data in active_patients.items():
            arrival_time = patient_data.get('arrival_time', datetime.utcnow())
            if isinstance(arrival_time, str):
                arrival_time = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
            duration = int((datetime.utcnow() - arrival_time).total_seconds() / 60)
            
            case = PatientCase(
                id=patient_id,
                type=patient_data.get("protocol", "General").upper(),
                duration=max(duration, 1),
                vitals={
                    "hr": patient_data.get("vitals", {}).get("hr", 80),
                    "bp_sys": patient_data.get("vitals", {}).get("bp_sys", 120),
                    "bp_dia": patient_data.get("vitals", {}).get("bp_dia", 80),
                    "spo2": patient_data.get("vitals", {}).get("spo2", 98),
                    "temp": patient_data.get("vitals", {}).get("temp", 37.0)
                },
                status=patient_data.get("status", "Pending"),
                location=f"ED-{len(cases) + 1}",
                lab_eta=patient_data.get("lab_eta", 10),
                assigned_bed=patient_data.get("assigned_bed", f"Bed-{len(cases) + 1}"),
                priority=1 if patient_data.get("acuity") == "1" else 3,
                timestamp=arrival_time,
                chief_complaint=patient_data.get("chief_complaint", ""),
                ems_report=patient_data.get("ems_report", "")
            )
            cases.append(case)
        
        # Apply filters
        if filters.case_type:
            cases = [case for case in cases if case.type == filters.case_type]
        if filters.status:
            cases = [case for case in cases if case.status == filters.status]
        if filters.priority:
            cases = [case for case in cases if case.priority == filters.priority]
        
        # Apply pagination
        start_idx = (pagination.page - 1) * pagination.limit
        end_idx = start_idx + pagination.limit
        cases = cases[start_idx:end_idx]
        
        logger.info(f"Retrieved {len(cases)} active cases")
        return cases
        
    except Exception as e:
        logger.error(f"Error retrieving active cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cases: {str(e)}")


@router.get("/activity", response_model=List[ActivityEntry])
async def get_recent_activity(
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    limit: int = Query(20, description="Maximum number of entries", ge=1, le=100)
):
    """
    Get recent activity log entries
    """
    try:
        # Generate sample activity entries
        activities = [
            ActivityEntry(
                id="system_1",
                timestamp=datetime.utcnow() - timedelta(minutes=1),
                type="System",
                message="LifeLink LangGraph pipeline ready",
                status="Ready"
            ),
            ActivityEntry(
                id="system_2",
                timestamp=datetime.utcnow() - timedelta(seconds=30),
                type="System",
                message="All 6 agent nodes active",
                status="Complete"
            )
        ]
        
        # Filter by activity type if specified
        if activity_type:
            activities = [a for a in activities if a.type.lower() == activity_type.lower()]
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        activities = activities[:limit]
        
        logger.info(f"Retrieved {len(activities)} activity entries")
        return activities
        
    except Exception as e:
        logger.error(f"Error retrieving activity log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve activity: {str(e)}")


@router.get("/status", response_model=ApiResponse)
async def get_dashboard_status():
    """
    Get overall dashboard status
    """
    try:
        active_patients = get_active_patients()
        
        status_data = {
            "agents_active": 6,
            "total_agents": 6,
            "active_cases": len(active_patients),
            "system_status": "operational",
            "pipeline": "LangGraph",
            "last_update": datetime.utcnow().isoformat()
        }
        
        return ApiResponse(
            success=True,
            message="Dashboard status retrieved successfully",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"Error retrieving dashboard status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve status: {str(e)}")
