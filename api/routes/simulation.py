"""
Simulation API Routes
Endpoints for triggering patient simulations (STEMI, Stroke, etc.)
Uses LangGraph pipeline for emergency coordination.
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.api_models import (
    SimulationRequest, SimulationResponse, CaseType, ApiResponse
)
from src.models import PatientArrivalNotification
from src.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Dependency to get shared state and services
def get_active_patients():
    from api.main import get_active_patients
    return get_active_patients()

def get_websocket_manager():
    from api.main import get_websocket_manager
    return get_websocket_manager()

def get_process_ambulance_case():
    from api.main import process_ambulance_case
    return process_ambulance_case


async def _run_lifelink_pipeline(
    patient_id: str,
    patient_data: PatientArrivalNotification,
    case_type: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Run the LangGraph pipeline for a patient case.
    
    Args:
        patient_id: Unique patient identifier
        patient_data: Patient arrival notification data
        case_type: Type of case (STEMI, Stroke, Trauma, etc.)
        background_tasks: FastAPI background tasks
        
    Returns:
        Pipeline result dictionary
    """
    active_patients = get_active_patients()
    ws_manager = get_websocket_manager()
    process_case = get_process_ambulance_case()
    
    # Build ambulance report text from patient data
    ambulance_text = f"""
AMBULANCE REPORT - {case_type.upper()} ALERT
Patient ID: {patient_id}
Time: {datetime.utcnow().isoformat()}

PATIENT DEMOGRAPHICS:
- Age: {patient_data.demographics.get('age', 'Unknown') if patient_data.demographics else 'Unknown'}
- Gender: {patient_data.demographics.get('gender', 'Unknown') if patient_data.demographics else 'Unknown'}
- Weight: {patient_data.demographics.get('weight', 'Unknown') if patient_data.demographics else 'Unknown'} kg

VITAL SIGNS:
- Heart Rate: {patient_data.vitals.get('hr', 'N/A')} bpm
- Blood Pressure: {patient_data.vitals.get('bp_sys', 'N/A')}/{patient_data.vitals.get('bp_dia', 'N/A')} mmHg
- SpO2: {patient_data.vitals.get('spo2', 'N/A')}%
- Temperature: {patient_data.vitals.get('temp', 'N/A')}°C

CHIEF COMPLAINT: {patient_data.chief_complaint}

EMS REPORT: {patient_data.ems_report}

PRIORITY: {patient_data.priority}
"""

    # Run the LangGraph pipeline
    logger.info(f"Running LangGraph pipeline for patient {patient_id}")
    result = await process_case(ambulance_text)
    
    # Extract protocol from result
    protocol = result.get("protocol_name", case_type.lower())
    
    # Store patient in active patients
    active_patients[patient_id] = {
        "acuity": "1" if patient_data.priority == 1 else str(patient_data.priority),
        "protocol": protocol,
        "status": "Triaged",
        "arrival_time": datetime.utcnow(),
        "vitals": patient_data.vitals,
        "chief_complaint": patient_data.chief_complaint,
        "ems_report": patient_data.ems_report,
        "lab_eta": 8,
        "assigned_bed": f"ED-{len(active_patients) + 1}",
        "ai_analysis": result.get("ai_analysis"),
        "agent_reports": result.get("agent_reports", {}),
        "final_response": result.get("final_response", ""),
        "errors": result.get("errors", [])
    }
    
    # Broadcast patient arrival via WebSocket
    background_tasks.add_task(
        ws_manager.broadcast_patient_arrival,
        {
            "patient_id": patient_id,
            "type": case_type.upper(),
            "vitals": patient_data.vitals,
            "status": "Triaged",
            "protocol": protocol
        }
    )
    
    # Broadcast protocol activation
    background_tasks.add_task(
        ws_manager.broadcast_protocol_activation,
        {
            "patient_id": patient_id,
            "protocol": protocol.upper() if protocol else case_type.upper(),
            "activation_time": datetime.utcnow().isoformat(),
            "target_completion": (datetime.utcnow().timestamp() + 300),
            "priority": patient_data.priority
        }
    )
    
    # Broadcast agent activities from the pipeline
    agent_reports = result.get("agent_reports", {})
    for agent_name, report in agent_reports.items():
        background_tasks.add_task(
            ws_manager.broadcast_agent_activity,
            {
                "agent": agent_name,
                "patient_id": patient_id,
                "action": f"{agent_name} completed",
                "report_preview": report[:200] if report else "",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return result


@router.post("/stemi", response_model=SimulationResponse)
async def simulate_stemi(background_tasks: BackgroundTasks):
    """
    Trigger STEMI patient simulation using LangGraph pipeline.
    
    Returns:
        SimulationResponse: Simulation result with patient details
    """
    try:
        # Generate unique patient ID
        patient_id = f"STEMI_{datetime.utcnow().strftime('%H%M%S')}"
        
        # Create STEMI patient data
        patient_data = PatientArrivalNotification(
            patient_id=patient_id,
            arrival_time=datetime.utcnow(),
            vitals={
                "hr": 110,
                "bp_sys": 160,
                "bp_dia": 95,
                "spo2": 94,
                "temp": 37.2
            },
            chief_complaint="Severe chest pain radiating to left arm and jaw",
            ems_report="72-year-old male with crushing chest pain, ST elevation on ECG, suspected STEMI",
            priority=1,
            demographics={
                "age": 72,
                "gender": "male",
                "weight": 80
            }
        )
        
        # Run LangGraph pipeline
        logger.info(f"Processing STEMI simulation for patient {patient_id}")
        result = await _run_lifelink_pipeline(patient_id, patient_data, "STEMI", background_tasks)
        
        response = SimulationResponse(
            message="STEMI simulation triggered successfully",
            patient_id=patient_id,
            case_type=CaseType.STEMI,
            timestamp=datetime.utcnow(),
            success=True
        )
        
        logger.info(f"STEMI simulation completed for patient {patient_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in STEMI simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"STEMI simulation failed: {str(e)}")


@router.post("/stroke", response_model=SimulationResponse)
async def simulate_stroke(background_tasks: BackgroundTasks):
    """
    Trigger Stroke patient simulation using LangGraph pipeline.
    
    Returns:
        SimulationResponse: Simulation result with patient details
    """
    try:
        # Generate unique patient ID
        patient_id = f"STROKE_{datetime.utcnow().strftime('%H%M%S')}"
        
        # Create Stroke patient data
        patient_data = PatientArrivalNotification(
            patient_id=patient_id,
            arrival_time=datetime.utcnow(),
            vitals={
                "hr": 80,
                "bp_sys": 195,
                "bp_dia": 118,
                "spo2": 96,
                "temp": 36.8
            },
            chief_complaint="Sudden onset weakness and speech difficulty",
            ems_report="68-year-old female with left-sided weakness, NIHSS 8, suspected stroke",
            priority=1,
            demographics={
                "age": 68,
                "gender": "female",
                "weight": 65
            }
        )
        
        # Run LangGraph pipeline
        logger.info(f"Processing Stroke simulation for patient {patient_id}")
        result = await _run_lifelink_pipeline(patient_id, patient_data, "Stroke", background_tasks)
        
        response = SimulationResponse(
            message="Stroke simulation triggered successfully",
            patient_id=patient_id,
            case_type=CaseType.STROKE,
            timestamp=datetime.utcnow(),
            success=True
        )
        
        logger.info(f"Stroke simulation completed for patient {patient_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in Stroke simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stroke simulation failed: {str(e)}")


@router.post("/trauma", response_model=SimulationResponse)
async def simulate_trauma(background_tasks: BackgroundTasks):
    """
    Trigger Trauma patient simulation using LangGraph pipeline.
    
    Returns:
        SimulationResponse: Simulation result with patient details
    """
    try:
        # Generate unique patient ID
        patient_id = f"TRAUMA_{datetime.utcnow().strftime('%H%M%S')}"
        
        # Create Trauma patient data
        patient_data = PatientArrivalNotification(
            patient_id=patient_id,
            arrival_time=datetime.utcnow(),
            vitals={
                "hr": 120,
                "bp_sys": 90,
                "bp_dia": 60,
                "spo2": 92,
                "temp": 36.5
            },
            chief_complaint="Multiple injuries from motor vehicle accident",
            ems_report="25-year-old male, high-speed MVA, multiple trauma, GCS 14",
            priority=1,
            demographics={
                "age": 25,
                "gender": "male",
                "weight": 75
            }
        )
        
        # Run LangGraph pipeline
        logger.info(f"Processing Trauma simulation for patient {patient_id}")
        result = await _run_lifelink_pipeline(patient_id, patient_data, "Trauma", background_tasks)
        
        response = SimulationResponse(
            message="Trauma simulation triggered successfully",
            patient_id=patient_id,
            case_type=CaseType.TRAUMA,
            timestamp=datetime.utcnow(),
            success=True
        )
        
        logger.info(f"Trauma simulation completed for patient {patient_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in Trauma simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trauma simulation failed: {str(e)}")


@router.post("/custom", response_model=SimulationResponse)
async def simulate_custom_case(
    request: SimulationRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger custom patient simulation using LangGraph pipeline.
    
    Args:
        request: Custom simulation parameters
        
    Returns:
        SimulationResponse: Simulation result with patient details
    """
    try:
        # Generate unique patient ID
        patient_id = f"{request.case_type.upper()}_{datetime.utcnow().strftime('%H%M%S')}"
        
        # Use provided patient data or defaults
        patient_data_dict = request.patient_data or {}
        
        # Create patient notification
        patient_notification = PatientArrivalNotification(
            patient_id=patient_id,
            arrival_time=datetime.utcnow(),
            vitals=patient_data_dict.get("vitals", {
                "hr": 85,
                "bp_sys": 120,
                "bp_dia": 80,
                "spo2": 98,
                "temp": 37.0
            }),
            chief_complaint=patient_data_dict.get("chief_complaint", f"{request.case_type} patient"),
            ems_report=patient_data_dict.get("ems_report", f"Custom {request.case_type} simulation"),
            priority=patient_data_dict.get("priority", 2),
            demographics=patient_data_dict.get("demographics", {})
        )
        
        # Run LangGraph pipeline
        logger.info(f"Processing custom {request.case_type} simulation for patient {patient_id}")
        result = await _run_lifelink_pipeline(patient_id, patient_notification, request.case_type, background_tasks)
        
        response = SimulationResponse(
            message=f"{request.case_type} simulation triggered successfully",
            patient_id=patient_id,
            case_type=request.case_type,
            timestamp=datetime.utcnow(),
            success=True
        )
        
        logger.info(f"Custom {request.case_type} simulation completed for patient {patient_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in custom simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Custom simulation failed: {str(e)}")


@router.post("/trigger")
async def trigger_simulation(
    request: dict,
    background_tasks: BackgroundTasks
):
    """
    Trigger simulation with raw ambulance report text.
    
    Args:
        request: Dict with "ambulance_report" key
        
    Returns:
        Full LangGraph pipeline result
    """
    try:
        ambulance_report = request.get("ambulance_report", "")
        if not ambulance_report:
            raise HTTPException(status_code=400, detail="ambulance_report is required")
        
        # Get the process function
        process_case = get_process_ambulance_case()
        ws_manager = get_websocket_manager()
        active_patients = get_active_patients()
        
        # Generate patient ID
        patient_id = f"CASE_{datetime.utcnow().strftime('%H%M%S')}"
        
        logger.info(f"Running LangGraph pipeline for {patient_id}")
        
        # Run the LangGraph pipeline
        result = await process_case(ambulance_report)
        
        protocol = result.get("protocol_name", "General")
        
        # Store in active patients
        active_patients[patient_id] = {
            "acuity": "1",
            "protocol": protocol,
            "status": "Triaged",
            "arrival_time": datetime.utcnow(),
            "vitals": {"hr": 100, "bp_sys": 140, "bp_dia": 90, "spo2": 95, "temp": 37.0},
            "chief_complaint": ambulance_report[:100],
            "ems_report": ambulance_report,
            "ai_analysis": result.get("ai_analysis"),
            "agent_reports": result.get("agent_reports", {}),
            "final_response": result.get("final_response", ""),
            "errors": result.get("errors", [])
        }
        
        # Broadcast via WebSocket
        background_tasks.add_task(
            ws_manager.broadcast_patient_arrival,
            {
                "patient_id": patient_id,
                "type": protocol.upper(),
                "status": "Triaged",
                "protocol": protocol
            }
        )
        
        logger.info(f"Pipeline completed for {patient_id}: Protocol={protocol}")
        
        return {
            "success": True,
            "patient_id": patient_id,
            "protocol": protocol,
            "ai_analysis": result.get("ai_analysis"),
            "agent_reports": result.get("agent_reports", {}),
            "final_response": result.get("final_response", ""),
            "errors": result.get("errors", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in trigger simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/status", response_model=ApiResponse)
async def get_simulation_status():
    """
    Get simulation system status
    
    Returns:
        ApiResponse: Simulation system status
    """
    try:
        active_patients = get_active_patients()
        
        # Get simulation statistics
        active_simulations = len(active_patients)
        
        status_data = {
            "simulation_system": "operational",
            "pipeline": "LangGraph",
            "active_simulations": active_simulations,
            "available_types": ["STEMI", "Stroke", "Trauma", "General", "Pediatric"],
            "last_simulation": datetime.utcnow().isoformat()
        }
        
        return ApiResponse(
            success=True,
            message="Simulation status retrieved successfully",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"Error retrieving simulation status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve simulation status: {str(e)}")
