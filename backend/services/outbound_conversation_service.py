"""
Outbound Conversation Service
Handles AI-initiated conversations with patients for reminders
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models
from services import reminder_service, patient_memory_service
from ai.agent import run_agent
from ai.memory import clear_memory, update_memory
from utils.language import translate_from_english
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OutboundConversation:
    """Manages an outbound conversation with a patient"""
    
    def __init__(self, appointment_data: dict, db: Session):
        self.appointment_data = appointment_data
        self.db = db
        self.session_id = f"outbound_{appointment_data['appointment_id']}_{uuid.uuid4().hex[:8]}"
        self.patient_id = appointment_data['patient_id']
        self.patient_language = appointment_data.get('patient_language', 'en')
        self.conversation_log = []
        
    def initiate_reminder_conversation(self):
        """Start the outbound reminder conversation"""
        
        # Clear any existing session memory
        clear_memory(self.session_id)
        
        # Set up session context
        update_memory(self.session_id, "patient_id", self.patient_id)
        update_memory(self.session_id, "appointment_id", self.appointment_data['appointment_id'])
        update_memory(self.session_id, "outbound_mode", True)
        update_memory(self.session_id, "conversation_type", "reminder")
        
        # Generate initial reminder message
        doctor_name = self.appointment_data.get('doctor_name', 'your doctor')
        appt_time = self.appointment_data.get('appointment_time', '')
        hours_until = self.appointment_data.get('hours_until', 0)
        
        # Format time nicely
        try:
            dt = datetime.strptime(appt_time, "%Y-%m-%d %H:%M")
            formatted_time = dt.strftime("%B %d at %I:%M %p")
        except:
            formatted_time = appt_time
        
        if hours_until < 2:
            urgency = "URGENT REMINDER"
            time_desc = "in less than 2 hours"
        elif hours_until < 24:
            urgency = "REMINDER"
            time_desc = f"in {int(hours_until)} hours"
        else:
            urgency = "REMINDER"
            time_desc = "tomorrow"
        
        initial_message = (
            f"{urgency}: You have an appointment with {doctor_name} on {formatted_time} "
            f"({time_desc}). Please reply with:\n"
            f"• 'CONFIRM' to confirm your appointment\n"
            f"• 'RESCHEDULE' to change the time\n"
            f"• 'CANCEL' to cancel the appointment"
        )
        
        if self.patient_language != "en":
            initial_message = translate_from_english(initial_message, self.patient_language)
        
        # Log the outbound message
        self.log_message("system", initial_message)
        
        return {
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "appointment_id": self.appointment_data['appointment_id'],
            "message": initial_message,
            "language": self.patient_language,
            "status": "sent",
            "conversation_type": "reminder_initiated"
        }
    
    def process_patient_response(self, patient_response: str):
        """Process patient's response to the reminder"""
        
        # Log patient response
        self.log_message("patient", patient_response)
        
        # Determine response type
        response_lower = patient_response.lower().strip()
        
        if any(word in response_lower for word in ['confirm', 'yes', 'ok', 'fine']):
            return self._handle_confirmation()
        elif any(word in response_lower for word in ['reschedule', 'change', 'move']):
            return self._handle_reschedule_request()
        elif any(word in response_lower for word in ['cancel', 'no', 'delete']):
            return self._handle_cancellation_request()
        else:
            return self._handle_complex_response(patient_response)
    
    def _handle_confirmation(self):
        """Handle appointment confirmation"""
        
        response_message = (
            "Thank you for confirming your appointment. "
            "We look forward to seeing you. Please arrive 10 minutes early."
        )
        
        # Translate if needed
        if self.patient_language != "en":
            response_message = translate_from_english(response_message, self.patient_language)
        
        # ).first()
        # if appointment:
        #     appointment.status = "confirmed"
        #     self.db.commit()
        
        self.log_message("system", response_message)
        
        return {
            "session_id": self.session_id,
            "action": "confirmed",
            "message": response_message,
            "status": "completed"
        }
    
    def _handle_reschedule_request(self):
        """Handle reschedule request"""
        
        response_message = (
            "I can help you reschedule your appointment. "
            "What day and time would work better for you?"
        )
        
        # Translate if needed
        if self.patient_language != "en":
            response_message = translate_from_english(response_message, self.patient_language)
        
        # Update session to reschedule mode
        update_memory(self.session_id, "intent", "reschedule_appointment")
        update_memory(self.session_id, "conversation_type", "reschedule")
        
        self.log_message("system", response_message)
        
        return {
            "session_id": self.session_id,
            "action": "reschedule_requested",
            "message": response_message,
            "status": "awaiting_new_time"
        }
    
    def _handle_cancellation_request(self):
        """Handle cancellation request"""
        
        response_message = (
            "I understand you want to cancel your appointment. "
            "Please reply 'YES CANCEL' to confirm the cancellation."
        )
        
        # Translate if needed
        if self.patient_language != "en":
            response_message = translate_from_english(response_message, self.patient_language)
        
        # Update session to cancellation mode
        update_memory(self.session_id, "intent", "cancel_appointment")
        update_memory(self.session_id, "conversation_type", "cancel_confirmation")
        
        self.log_message("system", response_message)
        
        return {
            "session_id": self.session_id,
            "action": "cancellation_requested",
            "message": response_message,
            "status": "awaiting_confirmation"
        }
    
    def _handle_complex_response(self, patient_response: str):
        """Use AI agent to handle complex responses"""
        
        # Set up context for AI agent
        update_memory(self.session_id, "outbound_context", {
            "appointment_id": self.appointment_data['appointment_id'],
            "doctor_name": self.appointment_data.get('doctor_name'),
            "appointment_time": self.appointment_data.get('appointment_time'),
            "is_outbound_conversation": True
        })
        
        # Process through AI agent
        agent_result = run_agent(patient_response, self.session_id)
        
        # Extract response message
        response_message = agent_result.get("message", "I didn't understand. Please reply CONFIRM, RESCHEDULE, or CANCEL.")
        
        # Translate if needed
        if self.patient_language != "en":
            response_message = translate_from_english(response_message, self.patient_language)
        
        self.log_message("system", response_message)
        
        return {
            "session_id": self.session_id,
            "action": "ai_handled",
            "message": response_message,
            "agent_result": agent_result,
            "status": "ongoing"
        }
    
    def log_message(self, sender: str, message: str):
        """Log conversation messages"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "sender": sender,  # "system", "patient", "ai"
            "message": message,
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "appointment_id": self.appointment_data['appointment_id']
        }
        
        self.conversation_log.append(log_entry)
        
        # Log to file/database
        logger.info(f"Outbound Conversation [{self.session_id}] {sender}: {message[:100]}...")
    
    def get_conversation_log(self):
        """Get the complete conversation log"""
        return self.conversation_log


def process_outbound_reminders(db: Session, hours_before: int = 24):
    """
    Main function to process all outbound reminders
    This would be called by a background job/cron
    """
    
    logger.info(f"Processing outbound reminders for appointments in next {hours_before} hours")
    
    # Get appointments needing reminders
    appointments = reminder_service.get_appointments_needing_reminder(db, hours_before)
    
    results = []
    
    for appointment in appointments:
        try:
            # Create outbound conversation
            conversation = OutboundConversation(appointment, db)
            
            # Initiate reminder
            result = conversation.initiate_reminder_conversation()
            
            # Store conversation for tracking
            results.append({
                "appointment_id": appointment['appointment_id'],
                "patient_id": appointment['patient_id'],
                "patient_name": appointment['patient_name'],
                "session_id": result['session_id'],
                "status": "reminder_sent",
                "message": result['message'],
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Reminder sent to patient {appointment['patient_id']} for appointment {appointment['appointment_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send reminder for appointment {appointment['appointment_id']}: {str(e)}")
            results.append({
                "appointment_id": appointment['appointment_id'],
                "patient_id": appointment['patient_id'],
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    return {
        "total_processed": len(appointments),
        "successful": len([r for r in results if r['status'] == 'reminder_sent']),
        "failed": len([r for r in results if r['status'] == 'failed']),
        "results": results
    }


def handle_outbound_response(db: Session, session_id: str, patient_response: str):
    """
    Handle patient response to outbound reminder
    This would be called when patient replies via SMS/call/etc.
    """
    
    if not session_id.startswith("outbound_"):
        return {"error": "Invalid outbound session ID"}
    
    try:
        appointment_id = int(session_id.split("_")[1])
    except:
        return {"error": "Could not extract appointment ID from session"}
    
    # Get appointment data
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()
    
    if not appointment:
        return {"error": "Appointment not found"}
    
    # Get patient and doctor info
    patient = db.query(models.Patient).filter(
        models.Patient.id == appointment.patient_id
    ).first()
    
    doctor = db.query(models.Doctor).filter(
        models.Doctor.id == appointment.doctor_id
    ).first()
    
    # Reconstruct appointment data
    appointment_data = {
        "appointment_id": appointment.id,
        "patient_id": appointment.patient_id,
        "patient_name": patient.name if patient else "Unknown",
        "patient_language": patient.language if patient else "en",
        "doctor_name": doctor.name if doctor else "Unknown",
        "appointment_time": appointment.time
    }
    
    # Create conversation handler
    conversation = OutboundConversation(appointment_data, db)
    conversation.session_id = session_id  # Use existing session
    
    # Process response
    result = conversation.process_patient_response(patient_response)
    
    return result