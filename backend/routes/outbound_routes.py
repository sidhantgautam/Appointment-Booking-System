"""
Outbound conversation routes for AI-initiated reminders
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from db.db import get_db
from services.outbound_conversation_service import (
    process_outbound_reminders, 
    handle_outbound_response,
    OutboundConversation
)
from services.performance_monitor import PerformanceMonitor
import models

router = APIRouter(prefix="/outbound", tags=["Outbound Conversations"])


class OutboundReminderRequest(BaseModel):
    hours_before: int = 24


class PatientResponseRequest(BaseModel):
    session_id: str
    patient_response: str


@router.post("/reminders/send")
def send_outbound_reminders(
    request: OutboundReminderRequest,
    db: Session = Depends(get_db)
):
    """
    Manually trigger outbound reminders for appointments
    This endpoint can be called by cron jobs or manual triggers
    """
    
    try:
        result = process_outbound_reminders(db, request.hours_before)
        
        return {
            "success": True,
            "message": f"Processed {result['total_processed']} appointments",
            "summary": {
                "total_processed": result['total_processed'],
                "successful": result['successful'],
                "failed": result['failed']
            },
            "results": result['results']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reminders: {str(e)}")


@router.post("/reminders/urgent")
def send_urgent_reminders(db: Session = Depends(get_db)):
    """Send urgent reminders (2 hours before appointments)"""
    
    try:
        result = process_outbound_reminders(db, hours_before=2)
        
        return {
            "success": True,
            "message": f"Sent {result['successful']} urgent reminders",
            "summary": {
                "total_processed": result['total_processed'],
                "successful": result['successful'],
                "failed": result['failed']
            },
            "results": result['results']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send urgent reminders: {str(e)}")


@router.post("/response")
def handle_patient_response(
    request: PatientResponseRequest,
    db: Session = Depends(get_db)
):
    """
    Handle patient response to outbound reminder
    This would be called when patient replies via SMS, call, or other channel
    """
    
    try:
        result = handle_outbound_response(
            db, 
            request.session_id, 
            request.patient_response
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "session_id": request.session_id,
            "patient_response": request.patient_response,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to handle response: {str(e)}")


@router.get("/conversation/{session_id}")
def get_conversation_log(session_id: str, db: Session = Depends(get_db)):
    """Get conversation log for an outbound session"""
    
    if not session_id.startswith("outbound_"):
        raise HTTPException(status_code=400, detail="Invalid outbound session ID")
    
    try:
        # Extract appointment ID from session
        appointment_id = int(session_id.split("_")[1])
        
        # Get appointment data
        appointment = db.query(models.Appointment).filter(
            models.Appointment.id == appointment_id
        ).first()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Get patient and doctor info
        patient = db.query(models.Patient).filter(
            models.Patient.id == appointment.patient_id
        ).first()
        
        doctor = db.query(models.Doctor).filter(
            models.Doctor.id == appointment.doctor_id
        ).first()
        
        return {
            "session_id": session_id,
            "appointment": {
                "id": appointment.id,
                "patient_name": patient.name if patient else "Unknown",
                "doctor_name": doctor.name if doctor else "Unknown",
                "appointment_time": appointment.time
            },
            "message": "Conversation log would be retrieved from storage/database"
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.get("/performance/stats")
def get_outbound_performance_stats():
    """Get performance statistics for outbound conversations"""
    
    try:
        stats = PerformanceMonitor.get_performance_stats(hours=24)
        
        return {
            "success": True,
            "performance_stats": stats,
            "message": "Performance statistics for last 24 hours"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")


@router.post("/test/conversation")
def test_outbound_conversation(db: Session = Depends(get_db)):
    """Test endpoint to create a mock outbound conversation"""
    
    try:
        # Create mock appointment data
        appointment_data = {
            "appointment_id": 999,
            "patient_id": 1,
            "patient_name": "Test Patient",
            "patient_language": "en",
            "doctor_name": "Dr Test",
            "appointment_time": "2026-03-15 10:00",
            "hours_until": 2.5
        }
        
        # Create conversation
        conversation = OutboundConversation(appointment_data, db)
        
        # Initiate reminder
        result = conversation.initiate_reminder_conversation()
        
        return {
            "success": True,
            "message": "Test conversation created successfully",
            "conversation": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create test conversation: {str(e)}")