"""
LifeLink external service clients.

This module provides async clients for external services:
- JSONBin for hospital data storage
- Claude AI for ambulance report analysis
- Twilio for WhatsApp notifications
"""

import os
import logging
import base64
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class JSONBinClient:
    """Async client for JSONBin hospital data operations."""
    
    def __init__(self):
        self.api_key = os.getenv(
            "JSONBIN_API_KEY", 
            "$2a$10$rwAXxHjp0m8RC1pL5BIW5.bc0orN3f3PivMK6lNPLOw1Gmh333uSa"
        )
        self.bin_id = os.getenv("JSONBIN_BIN_ID", "68fd4c71ae596e708f2c8fb0")
        self.base_url = "https://api.jsonbin.io/v3"
    
    async def get_hospital_data(self) -> dict:
        """
        Fetch current hospital data from JSONBin.
        
        Returns:
            dict: Hospital data including beds, staff, specialists, medications, etc.
                  Returns dict with "error" key if fetch fails.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/b/{self.bin_id}/latest",
                    headers={"X-Master-Key": self.api_key}
                )
                response.raise_for_status()
                return response.json()["record"]
        except httpx.TimeoutException:
            logger.error("JSONBin request timed out")
            return {"error": "Request timed out"}
        except httpx.HTTPStatusError as e:
            logger.error(f"JSONBin HTTP error: {e.response.status_code}")
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"JSONBin error: {str(e)}")
            return {"error": str(e)}
    
    async def update_hospital_data(self, data: dict) -> dict:
        """
        Update hospital data in JSONBin.
        
        Args:
            data: Updated hospital data
            
        Returns:
            dict: Response from JSONBin or dict with "error" key if update fails.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.base_url}/b/{self.bin_id}",
                    json=data,
                    headers={
                        "X-Master-Key": self.api_key,
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error("JSONBin update request timed out")
            return {"error": "Request timed out"}
        except httpx.HTTPStatusError as e:
            logger.error(f"JSONBin update HTTP error: {e.response.status_code}")
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"JSONBin update error: {str(e)}")
            return {"error": str(e)}



class GroqAnalyzer:
    """Groq AI integration for ambulance report analysis (free, fast inference)."""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = "llama-3.1-8b-instant"  # Fast, free model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def analyze_ambulance_report(
        self, 
        report: str, 
        hospital_status: dict
    ) -> dict:
        """
        Analyze ambulance report using Groq AI and determine protocol.
        
        Args:
            report: Ambulance report text
            hospital_status: Current hospital status from JSONBin
            
        Returns:
            dict with keys:
            - protocol: str (STEMI, Stroke, Trauma, General)
            - urgency: int (1-5, 1=critical)
            - analysis: str (detailed analysis text)
        """
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set, using fallback protocol detection")
            return self._fallback_analysis(report)
        
        try:
            current_status = hospital_status.get("current_status", {})
            protocols = hospital_status.get("protocols", {})
            
            analysis_prompt = f"""You are the ED Coordinator AI analyzing an ambulance report.

Ambulance Report:
{report}

Current ED Status:
- Total Patients: {current_status.get('total_patients', 0)}
- Critical Patients: {current_status.get('critical_patients', 0)}
- ED Capacity: {current_status.get('ed_capacity_percent', 0)}%
- System Load: {current_status.get('system_load', 'unknown')}

Protocol Performance Today:
- STEMI: {protocols.get('stemi', {}).get('total_today', 0)} cases, {protocols.get('stemi', {}).get('avg_door_to_balloon_minutes', 0)}min avg
- Stroke: {protocols.get('stroke', {}).get('total_today', 0)} cases, {protocols.get('stroke', {}).get('avg_door_to_needle_minutes', 0)}min avg
- Trauma: {protocols.get('trauma', {}).get('total_today', 0)} cases, {protocols.get('trauma', {}).get('avg_response_time_minutes', 0)}min avg

Analyze and determine:
1. Which protocol to activate (STEMI/Stroke/Trauma/General)
2. Urgency level (1-5, 1=critical)
3. Key actions needed
4. Estimated time to treatment

Respond in this format:
PROTOCOL: [name]
URGENCY: [1-5]
ANALYSIS: [brief analysis]"""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a medical AI assistant for emergency department coordination."},
                            {"role": "user", "content": analysis_prompt}
                        ],
                        "max_tokens": 400,
                        "temperature": 0.7
                    }
                )
                response.raise_for_status()
                result = response.json()
                analysis_text = result["choices"][0]["message"]["content"]
                
                return self._parse_analysis(analysis_text)
                
        except httpx.TimeoutException:
            logger.error("Groq API request timed out")
            return self._fallback_analysis(report)
        except httpx.HTTPStatusError as e:
            logger.error(f"Groq API HTTP error: {e.response.status_code}")
            return self._fallback_analysis(report)
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            return self._fallback_analysis(report)
    
    def _parse_analysis(self, analysis_text: str) -> dict:
        """Parse AI response into structured format."""
        protocol = "General"
        urgency = 3
        
        # First, try to extract protocol from the PROTOCOL: line (most reliable)
        for line in analysis_text.split("\n"):
            line_upper = line.upper().strip()
            if line_upper.startswith("PROTOCOL:"):
                protocol_value = line.split(":", 1)[-1].strip().upper()
                if "STEMI" in protocol_value:
                    protocol = "STEMI"
                elif "STROKE" in protocol_value:
                    protocol = "Stroke"
                elif "TRAUMA" in protocol_value:
                    protocol = "Trauma"
                elif "GENERAL" in protocol_value:
                    protocol = "General"
                break
            elif "URGENCY:" in line_upper:
                try:
                    urgency_str = line.split(":")[-1].strip()
                    urgency = int(urgency_str[0])
                    urgency = max(1, min(5, urgency))
                except (ValueError, IndexError):
                    pass
        
        # Fallback: if no PROTOCOL: line found, check the first few lines for keywords
        if protocol == "General":
            first_lines = "\n".join(analysis_text.split("\n")[:5]).upper()
            if "TRAUMA" in first_lines and "NOT" not in first_lines:
                protocol = "Trauma"
            elif "STROKE" in first_lines and "NOT" not in first_lines:
                protocol = "Stroke"
            elif "STEMI" in first_lines and "NOT" not in first_lines:
                protocol = "STEMI"
        
        return {
            "protocol": protocol,
            "urgency": urgency,
            "analysis": analysis_text,
        }
    
    def _fallback_analysis(self, report: str) -> dict:
        """Fallback protocol detection based on keywords when Claude is unavailable."""
        report_lower = report.lower()
        
        if any(kw in report_lower for kw in ["chest pain", "stemi", "cardiac", "heart attack", "mi"]):
            protocol = "STEMI"
            urgency = 1
        elif any(kw in report_lower for kw in ["stroke", "facial droop", "slurred speech", "weakness"]):
            protocol = "Stroke"
            urgency = 1
        elif any(kw in report_lower for kw in ["trauma", "accident", "injury", "mva", "fall"]):
            protocol = "Trauma"
            urgency = 2
        else:
            protocol = "General"
            urgency = 3
        
        return {
            "protocol": protocol,
            "urgency": urgency,
            "analysis": f"Fallback analysis: {protocol} protocol detected based on keywords. Urgency: {urgency}",
        }



class TwilioWhatsAppClient:
    """Twilio WhatsApp notification client."""
    
    # Default medical staff contacts
    MEDICAL_STAFF_CONTACTS = {
        "cardiologist": "+14082109942",
        "neurologist": "+9082192446",
        "trauma_surgeon": "+14082109942",
        "pediatrician": "+16693409734",
        "on_call_doctor": "+14082109942",
        "charge_nurse": "+16693409734"
    }
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_WHATSAPP_FROM", "+14155238886")
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        # Set to "false" to disable actual WhatsApp sending (for testing/demo)
        self.enabled = os.getenv("WHATSAPP_ENABLED", "true").lower() == "true"
        
        if not self.account_sid or not self.auth_token:
            logger.warning("TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set - WhatsApp disabled")
            self.enabled = False
    
    async def send_notification(
        self, 
        phone: str, 
        message: str
    ) -> dict:
        """
        Send WhatsApp message via Twilio.
        
        Args:
            phone: Recipient phone number (with country code)
            message: Message content
            
        Returns:
            dict with keys:
            - status: "sent" or "failed"
            - phone: recipient phone
            - sid: Twilio message SID (if sent)
            - error: error message (if failed)
            - timestamp: ISO timestamp
        """
        from datetime import datetime
        
        # If WhatsApp is disabled, simulate success
        if not self.enabled:
            logger.info(f"WhatsApp DISABLED - Would send to {phone[-4:]}: {message[:50]}...")
            return {
                "status": "sent",
                "phone": phone,
                "sid": f"SIMULATED_{datetime.utcnow().timestamp()}",
                "timestamp": datetime.utcnow().isoformat(),
                "simulated": True
            }
        
        try:
            # Create Basic Auth header
            auth_string = f"{self.account_sid}:{self.auth_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Basic {auth_b64}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "From": f"whatsapp:{self.from_number}",
                        "To": f"whatsapp:{phone}",
                        "Body": message
                    }
                )
                
                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"WhatsApp sent successfully to {phone[-4:]}, SID: {result.get('sid', 'unknown')}")
                    return {
                        "status": "sent",
                        "phone": phone,
                        "sid": result.get("sid"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"Twilio API error: {response.status_code} - {response.text}")
                    return {
                        "status": "failed",
                        "phone": phone,
                        "error": f"HTTP {response.status_code}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"WhatsApp send to {phone} timed out")
            return {
                "status": "failed",
                "phone": phone,
                "error": "Request timed out",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"WhatsApp send failed: {str(e)}")
            return {
                "status": "failed",
                "phone": phone,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def send_protocol_notifications(
        self,
        protocol: str
    ) -> list[dict]:
        """
        Send WhatsApp notifications to appropriate staff based on protocol.
        
        Args:
            protocol: Protocol name (STEMI, Stroke, Trauma, General)
            
        Returns:
            list of notification results
        """
        notifications = []
        
        if protocol == "STEMI":
            # Notify cardiology team
            result = await self.send_notification(
                self.MEDICAL_STAFF_CONTACTS["cardiologist"],
                "🚨 STEMI ALERT - Patient arriving in 5 min. Cath lab activation required. Please respond."
            )
            notifications.append({"recipient": "Cardiologist", **result})
            
            result = await self.send_notification(
                self.MEDICAL_STAFF_CONTACTS["charge_nurse"],
                "🏥 STEMI Protocol Active - Prepare cardiac medications and cath lab"
            )
            notifications.append({"recipient": "Charge Nurse", **result})
            
        elif protocol == "Stroke":
            # Notify neurology team
            result = await self.send_notification(
                self.MEDICAL_STAFF_CONTACTS["neurologist"],
                "🧠 STROKE ALERT - Patient arriving in 5 min. CT scan and tPA ready. Please respond."
            )
            notifications.append({"recipient": "Neurologist", **result})
            
        elif protocol == "Trauma":
            # Notify trauma team
            result = await self.send_notification(
                self.MEDICAL_STAFF_CONTACTS["trauma_surgeon"],
                "🚑 TRAUMA ALERT - Patient arriving in 5 min. Trauma bay ready. Please respond."
            )
            notifications.append({"recipient": "Trauma Surgeon", **result})
            
        else:
            # General - notify on-call doctor
            result = await self.send_notification(
                self.MEDICAL_STAFF_CONTACTS["on_call_doctor"],
                "🏥 ED ALERT - Patient arriving. Please prepare for assessment."
            )
            notifications.append({"recipient": "On-Call Doctor", **result})
        
        return notifications
    
    def get_contacts_for_protocol(self, protocol: str) -> list[str]:
        """Get list of contact roles for a given protocol."""
        if protocol == "STEMI":
            return ["Cardiologist", "Charge Nurse"]
        elif protocol == "Stroke":
            return ["Neurologist"]
        elif protocol == "Trauma":
            return ["Trauma Surgeon"]
        else:
            return ["On-Call Doctor"]


# Backward compatibility alias
GeminiAnalyzer = GroqAnalyzer
