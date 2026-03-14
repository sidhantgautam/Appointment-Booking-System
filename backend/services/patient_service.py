from sqlalchemy.orm import Session
import models
from services import patient_memory_service

def create_patient(db: Session, name: str, language: str):
    patient = models.Patient(name=name, language=language)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    # Create initial patient memory
    patient_memory_service.create_patient_memory(
        db, 
        patient.id, 
        preferred_language=language
    )
    
    return patient


def get_patient_by_id(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()


def get_all_patients(db: Session):
    return db.query(models.Patient).all()


def get_patient_with_preferences(db: Session, patient_id: int):
    """Get patient with their stored preferences"""
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        return None
    
    preferences = patient_memory_service.get_patient_preferences_context(db, patient_id)
    
    return {
        "patient": patient,
        "preferences": preferences
    }