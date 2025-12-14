"""
WebSocket Manager for LifeLink
Handles real-time communication between LangGraph agents and React frontend
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
import socketio

from ..models.api_models import (
    WebSocketEvent, PatientArrivalEvent, ProtocolActivationEvent,
    CaseUpdateEvent, AgentMessageEvent, ChatMessage, MessageType
)
from src.utils import get_logger

logger = get_logger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and real-time events"""
    
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        self.connected_clients: Set[str] = set()
        self.agent_listeners: Dict[str, Any] = {}
        self.message_history: List[ChatMessage] = []
        self.setup_socket_handlers()
        
    def setup_socket_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection"""
            self.connected_clients.add(sid)
            logger.info(f"Client {sid} connected. Total clients: {len(self.connected_clients)}")
            
            # Send connection confirmation
            await self.sio.emit('connection_status', {
                'connected': True,
                'timestamp': datetime.utcnow().isoformat(),
                'client_id': sid
            }, room=sid)
            
            # Send recent message history
            if self.message_history:
                recent_messages = self.message_history[-10:]  # Last 10 messages
                await self.sio.emit('message_history', {
                    'messages': [self._serialize_message(msg) for msg in recent_messages]
                }, room=sid)
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            self.connected_clients.discard(sid)
            logger.info(f"Client {sid} disconnected. Total clients: {len(self.connected_clients)}")
        
        @self.sio.event
        async def send_message(sid, data):
            """Handle chat messages from frontend"""
            try:
                message_content = data.get('message', '').strip()
                sender = data.get('sender', 'User')
                
                if not message_content:
                    await self.sio.emit('error', {
                        'message': 'Message content cannot be empty'
                    }, room=sid)
                    return
                
                # Create chat message
                chat_message = ChatMessage(
                    id=f"msg_{datetime.utcnow().timestamp()}",
                    content=message_content,
                    timestamp=datetime.utcnow(),
                    sender=sender,
                    type=MessageType.USER
                )
                
                # Add to history
                self.message_history.append(chat_message)
                
                # Broadcast to all clients
                await self.broadcast_chat_message(chat_message)
                
                # Simulate agent response after a delay
                asyncio.create_task(self._simulate_agent_response(message_content))
                
                logger.info(f"Chat message from {sender}: {message_content[:50]}...")
                
            except Exception as e:
                logger.error(f"Error handling chat message: {str(e)}")
                await self.sio.emit('error', {
                    'message': f'Failed to process message: {str(e)}'
                }, room=sid)
        
        @self.sio.event
        async def request_dashboard_update(sid):
            """Handle dashboard update requests"""
            try:
                # Trigger dashboard data refresh
                await self.sio.emit('dashboard_refresh', {
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
            except Exception as e:
                logger.error(f"Error handling dashboard update request: {str(e)}")
        
        @self.sio.event
        async def join_room(sid, data):
            """Handle room joining for targeted updates"""
            try:
                room = data.get('room', 'general')
                await self.sio.enter_room(sid, room)
                logger.info(f"Client {sid} joined room {room}")
                
            except Exception as e:
                logger.error(f"Error joining room: {str(e)}")
        
        @self.sio.event
        async def leave_room(sid, data):
            """Handle room leaving"""
            try:
                room = data.get('room', 'general')
                await self.sio.leave_room(sid, room)
                logger.info(f"Client {sid} left room {room}")
                
            except Exception as e:
                logger.error(f"Error leaving room: {str(e)}")
    
    async def setup_agent_listeners(self, agents: Dict[str, Any]):
        """Setup listeners for agent events"""
        self.agent_listeners = agents
        logger.info(f"Setup listeners for {len(agents)} agents")
        
        # In a real implementation, you would setup actual listeners
        # to the LangGraph agent node events here
        # For now, we'll simulate this with periodic updates
        asyncio.create_task(self._periodic_agent_updates())
    
    async def _periodic_agent_updates(self):
        """Simulate periodic agent updates"""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                if self.connected_clients:
                    # Simulate agent activity
                    await self.broadcast_agent_activity({
                        'agent': 'system',
                        'message': 'System health check',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Error in periodic updates: {str(e)}")
    
    async def _simulate_agent_response(self, user_message: str):
        """Process user message through LangGraph pipeline and broadcast responses"""
        try:
            # Import the LangGraph pipeline
            from lifelink.graph import run_lifelink_case
            
            logger.info(f"Processing message through LangGraph: {user_message[:50]}...")
            
            # Run the LangGraph pipeline
            result = await run_lifelink_case(user_message)
            
            protocol = result.get("protocol_name", "General")
            ai_analysis = result.get("ai_analysis", {})
            agent_reports = result.get("agent_reports", {})
            final_response = result.get("final_response", "")
            
            # Send coordinator response first
            coordinator_msg = f"🚨 {protocol.upper()} PROTOCOL ACTIVATED\n\n{ai_analysis.get('analysis', 'Processing complete.')}"
            await self._send_agent_message("ED Coordinator", "ed_coordinator", coordinator_msg)
            
            await asyncio.sleep(0.5)
            
            # Send each agent's report
            for agent_name, report in agent_reports.items():
                # Extract a summary from the report (first 200 chars)
                summary = report[:300] + "..." if len(report) > 300 else report
                display_name = agent_name.replace("_", " ").title()
                await self._send_agent_message(display_name, agent_name, summary)
                await asyncio.sleep(0.3)
            
            logger.info(f"LangGraph pipeline completed: Protocol={protocol}")
            
        except Exception as e:
            logger.error(f"Error in LangGraph agent response: {str(e)}")
            # Fallback to simple response
            await self._send_agent_message("ED Coordinator", "ed_coordinator", 
                f"Message received. Processing request... (Error: {str(e)[:50]})")
    
    async def _simulate_multi_agent_coordination(self, patient_case: Dict[str, Any], original_message: str):
        """Simulate coordinated multi-agent response for patient arrivals"""
        try:
            protocol = patient_case['protocol']
            patient_id = patient_case['patient_id']
            
            # ED Coordinator responds first
            ed_response = f"Patient arrival processed. {protocol.upper()} protocol activated for {patient_id}. Coordinating care team now."
            await self._send_agent_message("ED Coordinator", "ed_coordinator", ed_response)
            
            # Delay between agent responses
            await asyncio.sleep(1)
            
            # Resource Manager responds
            resource_response = f"Bed {patient_id.split('_')[1][-2:]} prepared. Equipment checked and ready. Notifying receiving team."
            await self._send_agent_message("Resource Manager", "resource_manager", resource_response)
            
            await asyncio.sleep(1)
            
            # Protocol-specific agent responses
            if protocol == "stemi":
                specialist_response = "Interventional cardiologist Dr. Martinez contacted. Cath lab team assembling. ETA 3 minutes."
                await self._send_agent_message("Specialist Coordinator", "specialist_coordinator", specialist_response)
                
                await asyncio.sleep(0.5)
                lab_response = "Cardiac enzymes, CBC, BMP ordered STAT. Results in 15 minutes. Type & cross-match ready."
                await self._send_agent_message("Lab Service", "lab_service", lab_response)
                
                await asyncio.sleep(0.5)
                pharmacy_response = "Heparin, aspirin, and clopidogrel prepared. IV access kit ready for administration."
                await self._send_agent_message("Pharmacy", "pharmacy", pharmacy_response)
                
            elif protocol == "stroke":
                specialist_response = "Stroke team activated. Neurologist Dr. Chen en route. CT scan scheduled immediately."
                await self._send_agent_message("Specialist Coordinator", "specialist_coordinator", specialist_response)
                
                await asyncio.sleep(0.5)
                lab_response = "Coagulation studies ordered STAT. Glucose and electrolytes processing. Results in 12 minutes."
                await self._send_agent_message("Lab Service", "lab_service", lab_response)
                
                await asyncio.sleep(0.5)
                pharmacy_response = "tPA prepared and ready. Blood pressure medications on standby."
                await self._send_agent_message("Pharmacy", "pharmacy", pharmacy_response)
                
            elif protocol == "trauma":
                specialist_response = "Trauma surgeon Dr. Smith and orthopedic Dr. Johnson alerted. Both available and responding."
                await self._send_agent_message("Specialist Coordinator", "specialist_coordinator", specialist_response)
                
                await asyncio.sleep(0.5)
                lab_response = "Type & cross-match for 6 units. Trauma panel ordered STAT. Blood bank on standby."
                await self._send_agent_message("Lab Service", "lab_service", lab_response)
                
                await asyncio.sleep(0.5)
                pharmacy_response = "Trauma medications prepared. Blood products coordinated with blood bank."
                await self._send_agent_message("Pharmacy", "pharmacy", pharmacy_response)
                
            else:  # general case
                specialist_response = "On-call physician Dr. Wilson notified. Assessment team being assembled."
                await self._send_agent_message("Specialist Coordinator", "specialist_coordinator", specialist_response)
                
                await asyncio.sleep(0.5)
                lab_response = "Standard admission labs ordered. Processing time approximately 20 minutes."
                await self._send_agent_message("Lab Service", "lab_service", lab_response)
            
            # MISSING BED MANAGEMENT AGENT - ADD IT HERE
            await asyncio.sleep(1)
            bed_response = f"Bed {patient_case.get('assigned_bed', 'ED-1')} assigned and prepared. Room cleaned, monitoring equipment ready. Patient can be transferred immediately."
            await self._send_agent_message("Bed Management", "bed_management", bed_response)
            
        except Exception as e:
            logger.error(f"Error in multi-agent coordination: {str(e)}")
    
    async def _simulate_single_agent_response(self, user_message: str):
        """Simulate single agent response for non-patient messages"""
        try:
            # Determine which agent should respond based on message content
            agent_name = "ED Coordinator"
            agent_type = "ed_coordinator"
            
            if "lab" in user_message.lower():
                agent_name = "Lab Service"
                agent_type = "lab_service"
            elif "medication" in user_message.lower() or "drug" in user_message.lower():
                agent_name = "Pharmacy"
                agent_type = "pharmacy"
            elif "bed" in user_message.lower():
                agent_name = "Bed Management"
                agent_type = "bed_management"
            elif "doctor" in user_message.lower() or "specialist" in user_message.lower():
                agent_name = "Specialist Coordinator"
                agent_type = "specialist_coordinator"
            
            responses = [
                "Message received. Processing request...",
                "Acknowledged. Coordinating with relevant departments.",
                "Request understood. Initiating appropriate protocols.",
                "Confirmed. Updating patient status and notifying team.",
                "Received. Checking resource availability and scheduling."
            ]
            
            import random
            response_content = random.choice(responses)
            
            await self._send_agent_message(agent_name, agent_type, response_content)
            
        except Exception as e:
            logger.error(f"Error in single agent response: {str(e)}")
    
    async def _send_agent_message(self, agent_name: str, agent_type: str, content: str):
        """Send a message from a specific agent"""
        try:
            agent_message = ChatMessage(
                id=f"agent_{datetime.utcnow().timestamp()}",
                content=content,
                timestamp=datetime.utcnow(),
                sender=agent_name,
                type=MessageType.AGENT,
                agent_type=agent_type
            )
            
            # Add to history
            self.message_history.append(agent_message)
            
            # Broadcast to all clients
            await self.broadcast_chat_message(agent_message)
            
        except Exception as e:
            logger.error(f"Error sending agent message: {str(e)}")
    
    def _serialize_message(self, message: ChatMessage) -> Dict[str, Any]:
        """Serialize chat message for transmission"""
        return {
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'sender': message.sender,
            'type': message.type,
            'agent_type': message.agent_type
        }
    
    async def broadcast_patient_arrival(self, patient_data: Dict[str, Any]):
        """Broadcast new patient arrival to all connected clients"""
        try:
            event = PatientArrivalEvent(
                data=patient_data
            )
            
            await self.sio.emit('patient_arrival', {
                'type': 'patient_arrival',
                'data': patient_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Broadcasted patient arrival: {patient_data.get('patient_id')}")
            
        except Exception as e:
            logger.error(f"Error broadcasting patient arrival: {str(e)}")
    
    async def broadcast_protocol_activation(self, protocol_data: Dict[str, Any]):
        """Broadcast protocol activation to all connected clients"""
        try:
            event = ProtocolActivationEvent(
                data=protocol_data
            )
            
            await self.sio.emit('protocol_activation', {
                'type': 'protocol_activation',
                'data': protocol_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Broadcasted protocol activation: {protocol_data.get('protocol')}")
            
        except Exception as e:
            logger.error(f"Error broadcasting protocol activation: {str(e)}")
    
    async def broadcast_case_update(self, case_data: Dict[str, Any]):
        """Broadcast case status update to all connected clients"""
        try:
            event = CaseUpdateEvent(
                data=case_data
            )
            
            await self.sio.emit('case_update', {
                'type': 'case_update',
                'data': case_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Broadcasted case update: {case_data.get('case_id')}")
            
        except Exception as e:
            logger.error(f"Error broadcasting case update: {str(e)}")
    
    async def broadcast_agent_message(self, message_data: Dict[str, Any]):
        """Broadcast agent communication to all connected clients"""
        try:
            event = AgentMessageEvent(
                data=message_data
            )
            
            await self.sio.emit('agent_message', {
                'type': 'agent_message',
                'data': message_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Broadcasted agent message from: {message_data.get('agent')}")
            
        except Exception as e:
            logger.error(f"Error broadcasting agent message: {str(e)}")
    
    async def broadcast_chat_message(self, message: ChatMessage):
        """Broadcast chat message to all connected clients"""
        try:
            await self.sio.emit('chat_message', self._serialize_message(message))
            logger.info(f"Broadcasted chat message from {message.sender}")
            
        except Exception as e:
            logger.error(f"Error broadcasting chat message: {str(e)}")
    
    async def broadcast_agent_activity(self, activity_data: Dict[str, Any]):
        """Broadcast general agent activity"""
        try:
            await self.sio.emit('agent_activity', {
                'type': 'agent_activity',
                'data': activity_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error broadcasting agent activity: {str(e)}")
    
    async def broadcast_dashboard_update(self, update_data: Dict[str, Any]):
        """Broadcast dashboard data updates"""
        try:
            await self.sio.emit('dashboard_update', {
                'type': 'dashboard_update',
                'data': update_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Also emit a dashboard refresh event to trigger frontend data reload
            await self.sio.emit('dashboard_refresh', {
                'action': update_data.get('action', 'update'),
                'timestamp': datetime.utcnow().isoformat(),
                'refresh_metrics': True,
                'refresh_cases': True
            })
            
            logger.info("Broadcasted dashboard update and refresh")
            
        except Exception as e:
            logger.error(f"Error broadcasting dashboard update: {str(e)}")
    
    async def send_to_client(self, client_id: str, event: str, data: Dict[str, Any]):
        """Send event to specific client"""
        try:
            if client_id in self.connected_clients:
                await self.sio.emit(event, data, room=client_id)
                logger.info(f"Sent {event} to client {client_id}")
            else:
                logger.warning(f"Client {client_id} not connected")
                
        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {str(e)}")
    
    def get_connected_clients_count(self) -> int:
        """Get number of connected clients"""
        return len(self.connected_clients)
    
    def get_message_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent message history"""
        recent_messages = self.message_history[-limit:] if self.message_history else []
        return [self._serialize_message(msg) for msg in recent_messages]
    
    async def _parse_and_create_patient_case(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse chat message for patient arrival information and create case if detected"""
        try:
            message_lower = message.lower()
            
            # Check if message indicates patient arrival
            arrival_keywords = ["arriving", "patient", "coming", "admission", "case", "emergency"]
            if not any(keyword in message_lower for keyword in arrival_keywords):
                return None
            
            # Detect condition type
            condition_type = None
            if any(word in message_lower for word in ["stemi", "heart attack", "mi", "myocardial"]):
                condition_type = "stemi"
            elif any(word in message_lower for word in ["stroke", "cva", "cerebrovascular"]):
                condition_type = "stroke"
            elif any(word in message_lower for word in ["trauma", "accident", "injury", "mva"]):
                condition_type = "trauma"
            elif any(word in message_lower for word in ["pediatric", "child", "kid", "infant"]):
                condition_type = "pediatric"
            else:
                condition_type = "general"
            
            # Extract age if mentioned
            import re
            age_match = re.search(r'(\d+)\s*(?:year|yr|y\.o\.)', message_lower)
            age = int(age_match.group(1)) if age_match else None
            
            # Extract gender if mentioned
            gender = None
            if any(word in message_lower for word in ["male", "man", "boy"]):
                gender = "male"
            elif any(word in message_lower for word in ["female", "woman", "girl"]):
                gender = "female"
            
            # Create patient case using simulation logic
            patient_case = await self._create_patient_case_from_chat(condition_type, age, gender, message)
            
            if patient_case:
                logger.info(f"Created patient case from chat: {patient_case['patient_id']} ({condition_type})")
                return patient_case
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing patient case from message: {str(e)}")
            return None
    
    async def _create_patient_case_from_chat(self, condition_type: str, age: Optional[int], gender: Optional[str], original_message: str) -> Optional[Dict[str, Any]]:
        """Create a patient case based on parsed chat information"""
        try:
            from api.main import get_ed_coordinator
            
            ed_coordinator = get_ed_coordinator()
            if not ed_coordinator:
                return None
            
            # Generate patient ID
            patient_id = f"{condition_type.upper()}_{datetime.utcnow().strftime('%H%M%S')}"
            
            # Generate appropriate vitals based on condition
            vitals = self._generate_vitals_for_condition(condition_type, age)
            
            # Generate chief complaint and EMS report
            chief_complaint, ems_report = self._generate_clinical_details(condition_type, age, gender, original_message)
            
            # Add to ED Coordinator's active patients
            if not hasattr(ed_coordinator, 'active_patients'):
                ed_coordinator.active_patients = {}
            
            patient_data = {
                "acuity": "1" if condition_type in ["stemi", "stroke", "trauma"] else "2",
                "protocol": condition_type,
                "status": "Triaged",
                "arrival_time": datetime.utcnow(),
                "vitals": vitals,
                "chief_complaint": chief_complaint,
                "ems_report": ems_report,
                "lab_eta": self._get_lab_eta_for_condition(condition_type),
                "assigned_bed": f"ED-{len(ed_coordinator.active_patients) + 1}"
            }
            
            ed_coordinator.active_patients[patient_id] = patient_data
            
            # Broadcast patient arrival via WebSocket
            await self.broadcast_patient_arrival({
                "patient_id": patient_id,
                "type": condition_type.title(),
                "vitals": vitals,
                "status": "Triaged",
                "protocol": condition_type
            })
            
            # Broadcast case update for live cases grid
            await self.broadcast_case_update({
                "case_id": patient_id,
                "action": "new_case",
                "case_data": {
                    "id": patient_id,
                    "type": condition_type.upper(),
                    "duration": 1,
                    "vitals": vitals,
                    "status": "Triaged",
                    "location": patient_data["assigned_bed"],
                    "lab_eta": patient_data["lab_eta"],
                    "priority": 1 if condition_type in ["stemi", "stroke", "trauma"] else 3
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Broadcast protocol activation for critical cases
            if condition_type in ["stemi", "stroke", "trauma"]:
                target_times = {"stemi": 300, "stroke": 420, "trauma": 180}  # seconds
                await self.broadcast_protocol_activation({
                    "patient_id": patient_id,
                    "protocol": condition_type.title(),
                    "activation_time": datetime.utcnow().isoformat(),
                    "target_completion": datetime.utcnow().timestamp() + target_times.get(condition_type, 300),
                    "priority": 1
                })
            
            # Broadcast dashboard update to refresh metrics and cases
            await self.broadcast_dashboard_update({
                "action": "new_patient_case",
                "patient_id": patient_id,
                "protocol": condition_type,
                "active_cases_count": len(ed_coordinator.active_patients),
                "refresh_required": True
            })
            
            return {
                "patient_id": patient_id,
                "protocol": condition_type,
                "condition": condition_type.title(),
                "age": age,
                "gender": gender
            }
            
        except Exception as e:
            logger.error(f"Error creating patient case from chat: {str(e)}")
            return None
    
    def _generate_vitals_for_condition(self, condition_type: str, age: Optional[int]) -> Dict[str, Any]:
        """Generate appropriate vital signs based on condition type"""
        import random
        
        base_vitals = {
            "hr": 85,
            "bp_sys": 120,
            "bp_dia": 80,
            "spo2": 98,
            "temp": 37.0
        }
        
        if condition_type == "stemi":
            base_vitals.update({
                "hr": random.randint(100, 120),
                "bp_sys": random.randint(150, 170),
                "bp_dia": random.randint(90, 100),
                "spo2": random.randint(92, 96),
                "temp": random.uniform(36.8, 37.5)
            })
        elif condition_type == "stroke":
            base_vitals.update({
                "hr": random.randint(75, 90),
                "bp_sys": random.randint(180, 200),
                "bp_dia": random.randint(110, 125),
                "spo2": random.randint(94, 98),
                "temp": random.uniform(36.5, 37.2)
            })
        elif condition_type == "trauma":
            base_vitals.update({
                "hr": random.randint(110, 130),
                "bp_sys": random.randint(80, 100),
                "bp_dia": random.randint(50, 70),
                "spo2": random.randint(88, 94),
                "temp": random.uniform(36.0, 36.8)
            })
        elif condition_type == "pediatric" and age and age < 18:
            # Adjust vitals for pediatric patients
            if age < 2:
                base_vitals.update({
                    "hr": random.randint(120, 160),
                    "bp_sys": random.randint(80, 100),
                    "bp_dia": random.randint(50, 65)
                })
            elif age < 12:
                base_vitals.update({
                    "hr": random.randint(90, 120),
                    "bp_sys": random.randint(90, 110),
                    "bp_dia": random.randint(55, 70)
                })
        
        return base_vitals
    
    def _generate_clinical_details(self, condition_type: str, age: Optional[int], gender: Optional[str], original_message: str) -> tuple:
        """Generate chief complaint and EMS report based on condition"""
        age_str = f"{age}-year-old" if age else "adult"
        gender_str = gender if gender else "patient"
        
        if condition_type == "stemi":
            chief_complaint = "Severe chest pain radiating to left arm and jaw"
            ems_report = f"{age_str} {gender_str} with crushing chest pain, ST elevation on ECG, suspected STEMI"
        elif condition_type == "stroke":
            chief_complaint = "Sudden onset weakness and speech difficulty"
            ems_report = f"{age_str} {gender_str} with left-sided weakness, speech difficulties, suspected stroke"
        elif condition_type == "trauma":
            chief_complaint = "Multiple injuries from accident"
            ems_report = f"{age_str} {gender_str} with multiple trauma, mechanism of injury unclear"
        elif condition_type == "pediatric":
            chief_complaint = "Pediatric emergency"
            ems_report = f"{age_str} {gender_str} pediatric patient requiring immediate assessment"
        else:
            chief_complaint = "General emergency department presentation"
            ems_report = f"{age_str} {gender_str} presenting to ED - details from chat: {original_message[:100]}"
        
        return chief_complaint, ems_report
    
    def _get_lab_eta_for_condition(self, condition_type: str) -> int:
        """Get appropriate lab ETA based on condition type"""
        eta_map = {
            "stemi": 5,
            "stroke": 6,
            "trauma": 4,
            "pediatric": 8,
            "general": 12
        }
        return eta_map.get(condition_type, 10)