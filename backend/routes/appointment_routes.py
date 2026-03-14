from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.db import get_db
import services.appointment_service as appointment_service
from schemas.appointment_schema import DoctorCreate

from schemas.appointment_schema import AppointmentCreate
from schemas.appointment_schema import RescheduleAppointment

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/doctor")
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    return appointment_service.create_doctor(
        db, doctor.name, doctor.specialization
    )


@router.get("/doctors")
def list_doctors(db: Session = Depends(get_db)):
    return appointment_service.get_all_doctors(db)


@router.get("/doctors/detailed")
def list_doctors_detailed(db: Session = Depends(get_db)):
    """Get doctors with appointment counts and details"""
    return appointment_service.get_doctors_with_details(db)


@router.post("/book")
def book_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):
    return appointment_service.book_appointment(
        db,
        data.patient_id,
        data.doctor_id,
        data.time
    )


@router.get("/")
def list_appointments(db: Session = Depends(get_db)):
    return appointment_service.list_appointments(db)


@router.get("/patient/{patient_id}")
def get_patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    """Get all appointments for a specific patient"""
    return appointment_service.get_appointments_by_patient(db, patient_id)


@router.get("/upcoming")
def get_upcoming(patient_id: int = None, db: Session = Depends(get_db)):
    """Get upcoming appointments, optionally filtered by patient"""
    return appointment_service.get_upcoming_appointments(db, patient_id)


@router.put("/reschedule")
def reschedule(data: RescheduleAppointment, db: Session = Depends(get_db)):
    return appointment_service.reschedule_appointment(
        db,
        data.appointment_id,
        data.new_time
    )


@router.delete("/{appointment_id}")
def cancel(appointment_id: int, db: Session = Depends(get_db)):
    return appointment_service.cancel_appointment(db, appointment_id)



@router.get("/reminders")
def get_reminders(hours_before: int = 24, db: Session = Depends(get_db)):
    """Get appointments that need reminders within specified hours"""
    from services import reminder_service
    return reminder_service.get_appointments_needing_reminder(db, hours_before)


@router.post("/reminders/send")
def send_reminders(hours_before: int = 24, db: Session = Depends(get_db)):
    """Process and send all pending reminders"""
    from services import reminder_service
    return reminder_service.process_all_reminders(db, hours_before)


@router.post("/reminders/outbound")
def send_outbound_reminders(hours_before: int = 24, db: Session = Depends(get_db)):
    """Send AI-initiated outbound reminder conversations"""
    from services import outbound_conversation_service
    return outbound_conversation_service.process_outbound_reminders(db, hours_before)


@router.post("/reminders/outbound/response")
def handle_outbound_response(
    session_id: str,
    patient_response: str,
    db: Session = Depends(get_db)
):
    """Handle patient response to outbound reminder"""
    from services import outbound_conversation_service
    return outbound_conversation_service.handle_outbound_response(db, session_id, patient_response)
