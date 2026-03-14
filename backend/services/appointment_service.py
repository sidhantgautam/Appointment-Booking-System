from sqlalchemy.orm import Session
import models


def create_doctor(db: Session, name: str, specialization: str):
    doctor = models.Doctor(name=name, specialization=specialization)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def get_all_doctors(db: Session):
    return db.query(models.Doctor).all()


def get_doctors_with_details(db: Session):
    """Get all doctors with detailed information"""
    doctors = db.query(models.Doctor).all()
    result = []
    
    for doctor in doctors:
        # Count appointments for this doctor
        appointment_count = db.query(models.Appointment).filter(
            models.Appointment.doctor_id == doctor.id
        ).count()
        
        result.append({
            "id": doctor.id,
            "name": doctor.name,
            "specialization": doctor.specialization,
            "total_appointments": appointment_count
        })
    
    return result

def book_appointment(db: Session, patient_id: int, doctor_id: int, time: str):

    existing = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.time == time
    ).first()

    if existing:
        return {"error": "Doctor already has an appointment at this time"}

    appointment = models.Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        time=time
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return appointment


def list_appointments(db: Session):
    return db.query(models.Appointment).all()


def get_appointments_by_patient(db: Session, patient_id: int):
    """Get all appointments for a specific patient with doctor details"""
    appointments = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id
    ).all()
    
    result = []
    for appt in appointments:
        doctor = db.query(models.Doctor).filter(
            models.Doctor.id == appt.doctor_id
        ).first()
        
        result.append({
            "id": appt.id,
            "patient_id": appt.patient_id,
            "doctor_id": appt.doctor_id,
            "doctor_name": doctor.name if doctor else "Unknown",
            "specialization": doctor.specialization if doctor else "Unknown",
            "time": appt.time
        })
    
    return result


def get_upcoming_appointments(db: Session, patient_id: int = None):
    """Get upcoming appointments (future dates only)"""
    from datetime import datetime
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    query = db.query(models.Appointment).filter(
        models.Appointment.time >= now
    )
    
    if patient_id:
        query = query.filter(models.Appointment.patient_id == patient_id)
    
    appointments = query.order_by(models.Appointment.time).all()
    
    result = []
    for appt in appointments:
        doctor = db.query(models.Doctor).filter(
            models.Doctor.id == appt.doctor_id
        ).first()
        
        patient = db.query(models.Patient).filter(
            models.Patient.id == appt.patient_id
        ).first()
        
        result.append({
            "id": appt.id,
            "patient_id": appt.patient_id,
            "patient_name": patient.name if patient else "Unknown",
            "doctor_id": appt.doctor_id,
            "doctor_name": doctor.name if doctor else "Unknown",
            "specialization": doctor.specialization if doctor else "Unknown",
            "time": appt.time
        })
    
    return result

def reschedule_appointment(db: Session, appointment_id: int, new_time: str):

    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()

    if not appointment:
        return {"error": "Appointment not found"}

    # Check conflict
    conflict = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == appointment.doctor_id,
        models.Appointment.time == new_time
    ).first()

    if conflict:
        return {"error": "Doctor already booked at this time"}

    appointment.time = new_time
    db.commit()
    db.refresh(appointment)

    return appointment

def cancel_appointment(db: Session, appointment_id: int):

    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()

    if not appointment:
        return {"error": "Appointment not found"}

    db.delete(appointment)
    db.commit()

    return {"message": "Appointment cancelled successfully"}




def find_next_available_slot(db: Session, doctor_id: int, preferred_time: str):
    """Find the next available time slot for a doctor"""
    from datetime import datetime, timedelta
    from utils.time_parser import normalize_time
    
    # Parse the preferred time
    preferred_dt = datetime.strptime(preferred_time, "%Y-%m-%d %H:%M")
    
    for i in range(16):  # 16 * 30 min = 8 hours
        check_time = preferred_dt + timedelta(minutes=30 * i)
        check_time_str = check_time.strftime("%Y-%m-%d %H:%M")
        
        # Check if this slot is available
        existing = db.query(models.Appointment).filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.time == check_time_str
        ).first()
        
        if not existing:
            return check_time_str
    
    return None


def find_appointment_by_criteria(db: Session, patient_id: int = None, doctor_id: int = None, time: str = None):
    """Find appointment(s) matching the given criteria"""
    query = db.query(models.Appointment)
    
    if patient_id:
        query = query.filter(models.Appointment.patient_id == patient_id)
    if doctor_id:
        query = query.filter(models.Appointment.doctor_id == doctor_id)
    if time:
        query = query.filter(models.Appointment.time == time)
    
    return query.all()


def get_appointment_by_id(db: Session, appointment_id: int):
    """Get a specific appointment by ID"""
    return db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()


def find_doctor_by_specialization(db: Session, specialization: str):
    """Find doctors by specialization"""
    return db.query(models.Doctor).filter(
        models.Doctor.specialization.ilike(f"%{specialization}%")
    ).all()


def find_doctor_by_name_or_specialization(db: Session, search_term: str):
    """Find doctor by name or specialization"""
    # Try name first
    doctor = db.query(models.Doctor).filter(
        models.Doctor.name.ilike(f"%{search_term}%")
    ).first()
    
    if doctor:
        return doctor, "name"
    
    # Try specialization
    doctors = find_doctor_by_specialization(db, search_term)
    if doctors:
        return doctors, "specialization"
    
    return None, None
