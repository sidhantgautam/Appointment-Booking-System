"""
Appointment Reminder Service
Sends reminders before appointment time
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models


def get_appointments_needing_reminder(db: Session, hours_before: int = 24):
    """
    Get appointments that need reminders
    Returns appointments happening within the specified hours
    """
    now = datetime.now()
    reminder_window_start = now
    reminder_window_end = now + timedelta(hours=hours_before)
    
    start_str = reminder_window_start.strftime("%Y-%m-%d %H:%M")
    end_str = reminder_window_end.strftime("%Y-%m-%d %H:%M")
    
    appointments = db.query(models.Appointment).filter(
        models.Appointment.time >= start_str,
        models.Appointment.time <= end_str
    ).all()
    
    result = []
    for appt in appointments:
        doctor = db.query(models.Doctor).filter(
            models.Doctor.id == appt.doctor_id
        ).first()
        
        patient = db.query(models.Patient).filter(
            models.Patient.id == appt.patient_id
        ).first()
        
        # Calculate time until appointment
        appt_time = datetime.strptime(appt.time, "%Y-%m-%d %H:%M")
        time_until = appt_time - now
        hours_until = time_until.total_seconds() / 3600
        
        result.append({
            "appointment_id": appt.id,
            "patient_id": appt.patient_id,
            "patient_name": patient.name if patient else "Unknown",
            "patient_language": patient.language if patient else "English",
            "doctor_id": appt.doctor_id,
            "doctor_name": doctor.name if doctor else "Unknown",
            "specialization": doctor.specialization if doctor else "Unknown",
            "appointment_time": appt.time,
            "hours_until": round(hours_until, 1)
        })
    
    return result


def generate_reminder_message(appointment_data: dict, language: str = "English"):
    """Generate a reminder message for an appointment"""
    
    doctor_name = appointment_data.get("doctor_name", "your doctor")
    appt_time = appointment_data.get("appointment_time", "")
    hours_until = appointment_data.get("hours_until", 0)
    
    # Parse time for better formatting
    try:
        dt = datetime.strptime(appt_time, "%Y-%m-%d %H:%M")
        formatted_time = dt.strftime("%B %d at %I:%M %p")
    except:
        formatted_time = appt_time
    
    if hours_until < 1:
        urgency = "URGENT: "
        time_desc = "in less than an hour"
    elif hours_until < 3:
        urgency = "REMINDER: "
        time_desc = f"in {int(hours_until)} hours"
    elif hours_until < 24:
        urgency = "REMINDER: "
        time_desc = f"in {int(hours_until)} hours"
    else:
        urgency = "REMINDER: "
        time_desc = "tomorrow"
    
    message = f"{urgency}You have an appointment with {doctor_name} on {formatted_time} ({time_desc}). Please arrive 10 minutes early."
    
    return message


def send_reminder(appointment_data: dict):
    """
    Send reminder to patient
    In a real system, this would integrate with:
    - SMS service (Twilio)
    - Email service (SendGrid)
    - Push notifications
    - WhatsApp Business API
    """
    
    patient_name = appointment_data.get("patient_name")
    language = appointment_data.get("patient_language", "English")
    
    message = generate_reminder_message(appointment_data, language)
    
    return {
        "patient_id": appointment_data.get("patient_id"),
        "patient_name": patient_name,
        "message": message,
        "status": "pending",  # Would be "sent" after actual delivery
        "delivery_method": "sms",  # or "email", "push", etc.
    }


def process_all_reminders(db: Session, hours_before: int = 24):
    """
    Process all appointments needing reminders
    Returns list of reminders that were generated
    """
    appointments = get_appointments_needing_reminder(db, hours_before)
    reminders = []
    
    for appt in appointments:
        reminder = send_reminder(appt)
        reminders.append(reminder)
    
    return {
        "total_reminders": len(reminders),
        "reminders": reminders
    }
