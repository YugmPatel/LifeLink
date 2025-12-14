"""
Cases API Routes
Endpoints for patient case management and details.
Uses shared active_patients storage from main module.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Path, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.api_models import (
    PatientCase, CaseType, CaseStatus, ApiResponse, PatientVitals
)
from src.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Dependency to get shared state
def get_active_patients():
    from api.main import get_active_patients
    return get_active_patients()

def get_websocket_manager():
    from api.main import get_websocket_manager
    return get_websocket_manager()


@router.get("/", response_model=List[PatientCase])
async def get_all_cases(
    status: Optional[CaseStatus] = Query(None, description="Filter by case status"),
    case_type: Optional[CaseType] = Query(None, description="Filter by case type"),
    priority: Optional[int] = Query(None, description="Filter by priority (1-5)", ge=1, le=5),
    limit: int = Query(20, description="Maximum number of cases", ge=1, le=100)
):
    """
    Get all patient cases with optional filtering
    
    Args:
        status: Optional filter by case status
        case_type: Optional filter by case type
        priority: Optional filter by priority level
        limit: Maximum number of cases to return
        
    Returns:
        List[PatientCase]: List of patient cases
    """
    try:
        active_patients = get_active_patients()
        
        cases = []
        
        # Get cases from active patients storage
        for patient_id, patient_data in active_patients.items():
            # Calculate duration since arrival
            arrival_time = patient_data.get('arrival_time', datetime.utcnow())
            if isinstance(arrival_time, str):
                arrival_time = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
            duration = int((datetime.utcnow() - arrival_time).total_seconds() / 60)

            # Create case object
            # Normalize protocol to match CaseType enum
            protocol = patient_data.get("protocol", "General")
            protocol_map = {
                "stemi": "STEMI",
                "stroke": "Stroke", 
                "trauma": "Trauma",
                "general": "General",
                "pediatric": "Pediatric"
            }
            case_type = protocol_map.get(protocol.lower(), "General")
            
            case = PatientCase(
                id=patient_id,
                type=case_type,
                duration=max(duration, 1),
                vitals=PatientVitals(
                    hr=patient_data.get("vitals", {}).get("hr", 80),
                    bp_sys=patient_data.get("vitals", {}).get("bp_sys", 120),
                    bp_dia=patient_data.get("vitals", {}).get("bp_dia", 80),
                    spo2=patient_data.get("vitals", {}).get("spo2", 98),
                    temp=patient_data.get("vitals", {}).get("temp", 37.0)
                ),
                status=patient_data.get("status", "Pending"),
                location=patient_data.get("location", f"ED-{len(cases) + 1}"),
                lab_eta=patient_data.get("lab_eta", 10),
                assigned_bed=patient_data.get("assigned_bed", f"Bed-{len(cases) + 1}"),
                priority=1 if patient_data.get("acuity") == "1" else 3,
                timestamp=arrival_time,
                chief_complaint=patient_data.get("chief_complaint", ""),
                ems_report=patient_data.get("ems_report", "")
            )
            cases.append(case)
        
        # Apply filters
        if status:
            cases = [case for case in cases if case.status == status]
        if case_type:
            cases = [case for case in cases if case.type == case_type]
        if priority:
            cases = [case for case in cases if case.priority == priority]
        
        # Sort by priority and timestamp
        cases.sort(key=lambda x: (x.priority, x.timestamp), reverse=False)
        
        # Apply limit
        cases = cases[:limit]
        
        logger.info(f"Retrieved {len(cases)} cases")
        return cases
        
    except Exception as e:
        logger.error(f"Error retrieving cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cases: {str(e)}")


@router.get("/{case_id}", response_model=PatientCase)
async def get_case_details(
    case_id: str = Path(..., description="Case ID to retrieve")
):
    """
    Get detailed information for a specific case
    
    Args:
        case_id: The case ID to retrieve details for
        
    Returns:
        PatientCase: Detailed case information
    """
    try:
        active_patients = get_active_patients()
        
        patient_data = active_patients.get(case_id)
        if not patient_data:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        # Calculate duration since arrival
        arrival_time = patient_data.get('arrival_time', datetime.utcnow())
        if isinstance(arrival_time, str):
            arrival_time = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
        duration = int((datetime.utcnow() - arrival_time).total_seconds() / 60)
        
        # Create detailed case object
        case = PatientCase(
            id=case_id,
            type=patient_data.get("protocol", "General").upper(),
            duration=max(duration, 1),
            vitals=PatientVitals(
                hr=patient_data.get("vitals", {}).get("hr", 80),
                bp_sys=patient_data.get("vitals", {}).get("bp_sys", 120),
                bp_dia=patient_data.get("vitals", {}).get("bp_dia", 80),
                spo2=patient_data.get("vitals", {}).get("spo2", 98),
                temp=patient_data.get("vitals", {}).get("temp", 37.0)
            ),
            status=patient_data.get("status", "Pending"),
            location=patient_data.get("location", "ED-1"),
            lab_eta=patient_data.get("lab_eta", 10),
            assigned_bed=patient_data.get("assigned_bed", "Bed-1"),
            priority=1 if patient_data.get("acuity") == "1" else 3,
            timestamp=arrival_time,
            chief_complaint=patient_data.get("chief_complaint", ""),
            ems_report=patient_data.get("ems_report", "")
        )
        
        logger.info(f"Retrieved details for case {case_id}")
        return case
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve case {case_id}: {str(e)}")


@router.put("/{case_id}/status", response_model=ApiResponse)
async def update_case_status(
    case_id: str = Path(..., description="Case ID to update"),
    new_status: CaseStatus = Query(..., description="New case status"),
    background_tasks: BackgroundTasks = None
):
    """
    Update the status of a specific case
    
    Args:
        case_id: The case ID to update
        new_status: The new status to set
        background_tasks: Background tasks for WebSocket notifications
        
    Returns:
        ApiResponse: Update operation result
    """
    try:
        active_patients = get_active_patients()
        ws_manager = get_websocket_manager()
        
        patient_data = active_patients.get(case_id)
        if not patient_data:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        # Update status
        old_status = patient_data.get("status", "Unknown")
        patient_data["status"] = new_status
        patient_data["last_updated"] = datetime.utcnow()
        
        # Broadcast case update via WebSocket
        if background_tasks and ws_manager:
            background_tasks.add_task(
                ws_manager.broadcast_case_update,
                {
                    "case_id": case_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        logger.info(f"Updated case {case_id} status from {old_status} to {new_status}")
        
        return ApiResponse(
            success=True,
            message=f"Case {case_id} status updated to {new_status}",
            data={
                "case_id": case_id,
                "old_status": old_status,
                "new_status": new_status,
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating case {case_id} status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update case {case_id}: {str(e)}")


@router.delete("/{case_id}", response_model=ApiResponse)
async def discharge_case(
    case_id: str = Path(..., description="Case ID to discharge"),
    background_tasks: BackgroundTasks = None
):
    """
    Discharge a patient case (remove from active cases)
    
    Args:
        case_id: The case ID to discharge
        background_tasks: Background tasks for WebSocket notifications
        
    Returns:
        ApiResponse: Discharge operation result
    """
    try:
        active_patients = get_active_patients()
        ws_manager = get_websocket_manager()
        
        patient_data = active_patients.get(case_id)
        if not patient_data:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        # Remove from active patients
        discharged_patient = active_patients.pop(case_id)
        
        # Broadcast case discharge via WebSocket
        if background_tasks and ws_manager:
            background_tasks.add_task(
                ws_manager.broadcast_case_update,
                {
                    "case_id": case_id,
                    "action": "discharged",
                    "timestamp": datetime.utcnow().isoformat(),
                    "final_status": "Discharged"
                }
            )
        
        logger.info(f"Discharged case {case_id}")
        
        return ApiResponse(
            success=True,
            message=f"Case {case_id} discharged successfully",
            data={
                "case_id": case_id,
                "discharge_time": datetime.utcnow().isoformat(),
                "total_duration": discharged_patient.get("duration", 0)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discharging case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to discharge case {case_id}: {str(e)}")


@router.get("/statistics/summary", response_model=ApiResponse)
async def get_case_statistics():
    """
    Get case statistics and summary
    
    Returns:
        ApiResponse: Case statistics
    """
    try:
        active_patients = get_active_patients()
        
        cases = active_patients
        
        # Calculate statistics
        total_cases = len(cases)
        critical_cases = len([case for case in cases.values() if case.get("acuity") == "1"])
        
        # Count by protocol
        protocol_counts = {}
        for case in cases.values():
            protocol = case.get("protocol", "general")
            protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
        
        # Count by status
        status_counts = {}
        for case in cases.values():
            status = case.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate average duration
        durations = []
        for case in cases.values():
            arrival_time = case.get('arrival_time', datetime.utcnow())
            if isinstance(arrival_time, str):
                arrival_time = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
            duration = (datetime.utcnow() - arrival_time).total_seconds() / 60
            durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        stats_data = {
            "total_active_cases": total_cases,
            "critical_cases": critical_cases,
            "average_duration_minutes": round(avg_duration, 1),
            "protocol_breakdown": protocol_counts,
            "status_breakdown": status_counts,
            "last_updated": datetime.utcnow().isoformat(),
            "pipeline": "LangGraph",
            "system_capacity": {
                "current_load": total_cases,
                "max_capacity": 50,
                "utilization_percentage": (total_cases / 50) * 100
            }
        }
        
        return ApiResponse(
            success=True,
            message="Case statistics retrieved successfully",
            data=stats_data
        )
        
    except Exception as e:
        logger.error(f"Error retrieving case statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve case statistics: {str(e)}")


@router.post("/{case_id}/vitals", response_model=ApiResponse)
async def update_case_vitals(
    case_id: str = Path(..., description="Case ID to update"),
    vitals: PatientVitals = ...,
    background_tasks: BackgroundTasks = None
):
    """
    Update vital signs for a specific case
    
    Args:
        case_id: The case ID to update
        vitals: New vital signs data
        background_tasks: Background tasks for WebSocket notifications
        
    Returns:
        ApiResponse: Update operation result
    """
    try:
        active_patients = get_active_patients()
        ws_manager = get_websocket_manager()
        
        patient_data = active_patients.get(case_id)
        if not patient_data:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        # Update vitals
        old_vitals = patient_data.get("vitals", {})
        patient_data["vitals"] = vitals.dict()
        patient_data["vitals_last_updated"] = datetime.utcnow()
        
        # Broadcast vitals update via WebSocket
        if background_tasks and ws_manager:
            background_tasks.add_task(
                ws_manager.broadcast_case_update,
                {
                    "case_id": case_id,
                    "update_type": "vitals",
                    "old_vitals": old_vitals,
                    "new_vitals": vitals.dict(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        logger.info(f"Updated vitals for case {case_id}")
        
        return ApiResponse(
            success=True,
            message=f"Vitals updated for case {case_id}",
            data={
                "case_id": case_id,
                "vitals": vitals.dict(),
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vitals for case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update vitals for case {case_id}: {str(e)}")


@router.get("/{case_id}/timeline", response_model=ApiResponse)
async def get_case_timeline(
    case_id: str = Path(..., description="Case ID to get timeline for")
):
    """
    Get timeline of events for a specific case
    
    Args:
        case_id: The case ID to get timeline for
        
    Returns:
        ApiResponse: Case timeline data
    """
    try:
        active_patients = get_active_patients()
        
        patient_data = active_patients.get(case_id)
        if not patient_data:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        # Calculate arrival time
        arrival_time = patient_data.get('arrival_time', datetime.utcnow())
        if isinstance(arrival_time, str):
            arrival_time = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
        
        # Build timeline from LangGraph agent reports
        timeline = [
            {
                "timestamp": arrival_time.isoformat(),
                "event": "Patient Arrival",
                "description": f"Patient {case_id} arrived at ED",
                "agent": "System"
            },
            {
                "timestamp": (arrival_time + timedelta(minutes=1)).isoformat(),
                "event": "LangGraph Pipeline Started",
                "description": "Emergency coordination pipeline initiated",
                "agent": "LifeLink Coordinator"
            },
            {
                "timestamp": (arrival_time + timedelta(minutes=2)).isoformat(),
                "event": "Protocol Activated",
                "description": f"{patient_data.get('protocol', 'General').upper()} protocol initiated",
                "agent": "LifeLink Coordinator"
            }
        ]
        
        # Add agent report events from LangGraph results
        agent_reports = patient_data.get("agent_reports", {})
        offset = 3
        for agent_name, report in agent_reports.items():
            timeline.append({
                "timestamp": (arrival_time + timedelta(minutes=offset)).isoformat(),
                "event": f"{agent_name.replace('_', ' ').title()} Report",
                "description": report[:100] + "..." if len(report) > 100 else report,
                "agent": agent_name.replace('_', ' ').title()
            })
            offset += 1
        
        # Add protocol-specific events
        protocol = patient_data.get('protocol', 'general')
        if protocol == 'stemi':
            timeline.append({
                "timestamp": (arrival_time + timedelta(minutes=offset)).isoformat(),
                "event": "Cath Lab Notified",
                "description": "Interventional cardiology team activated",
                "agent": "Specialist Coordinator"
            })
        elif protocol == 'stroke':
            timeline.append({
                "timestamp": (arrival_time + timedelta(minutes=offset)).isoformat(),
                "event": "Stroke Team Activated",
                "description": "Neurology team notified",
                "agent": "Specialist Coordinator"
            })
        
        return ApiResponse(
            success=True,
            message=f"Timeline retrieved for case {case_id}",
            data={
                "case_id": case_id,
                "timeline": timeline,
                "total_events": len(timeline),
                "pipeline": "LangGraph"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving timeline for case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve timeline for case {case_id}: {str(e)}")


@router.get("/{case_id}/agent-reports", response_model=ApiResponse)
async def get_case_agent_reports(
    case_id: str = Path(..., description="Case ID to get agent reports for")
):
    """
    Get LangGraph agent reports for a specific case
    
    Args:
        case_id: The case ID to get agent reports for
        
    Returns:
        ApiResponse: Agent reports from LangGraph pipeline
    """
    try:
        active_patients = get_active_patients()
        
        patient_data = active_patients.get(case_id)
        if not patient_data:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        agent_reports = patient_data.get("agent_reports", {})
        ai_analysis = patient_data.get("ai_analysis", {})
        final_response = patient_data.get("final_response", "")
        errors = patient_data.get("errors", [])
        
        return ApiResponse(
            success=True,
            message=f"Agent reports retrieved for case {case_id}",
            data={
                "case_id": case_id,
                "protocol": patient_data.get("protocol"),
                "ai_analysis": ai_analysis,
                "agent_reports": agent_reports,
                "final_response": final_response,
                "errors": errors,
                "pipeline": "LangGraph"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving agent reports for case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent reports for case {case_id}: {str(e)}")
