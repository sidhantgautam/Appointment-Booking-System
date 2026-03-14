from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.db import get_db
import services.patient_service as patient_service
from services import patient_memory_service
from schemas.patient_schema import PatientCreate

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("/")
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    return patient_service.create_patient(db, patient.name, patient.language)


@router.get("/")
def list_patients(db: Session = Depends(get_db)):
    return patient_service.get_all_patients(db)


@router.get("/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return patient_service.get_patient_by_id(db, patient_id)


@router.get("/{patient_id}/preferences")
def get_patient_preferences(patient_id: int, db: Session = Depends(get_db)):
    """Get patient preferences and interaction history"""
    preferences = patient_memory_service.get_patient_preferences_context(db, patient_id)
    history = patient_memory_service.get_patient_interaction_history(db, patient_id)
    suggestions = patient_memory_service.suggest_based_on_history(db, patient_id)
    
    return {
        "patient_id": patient_id,
        "preferences": preferences,
        "interaction_history": history,
        "smart_suggestions": suggestions
    }


@router.put("/{patient_id}/preferences")
def update_patient_preferences(
    patient_id: int, 
    preferences: dict, 
    db: Session = Depends(get_db)
):
    """Manually update patient preferences"""
    updated_memory = patient_memory_service.update_patient_memory(
        db, patient_id, **preferences
    )
    
    return {
        "patient_id": patient_id,
        "message": "Preferences updated successfully",
        "updated_preferences": {
            "preferred_language": updated_memory.preferred_language,
            "preferred_doctor_name": updated_memory.preferred_doctor_name,
            "preferred_specialization": updated_memory.preferred_specialization,
            "preferred_time_slot": updated_memory.preferred_time_slot,
            "interaction_count": updated_memory.interaction_count
        }
    }


@router.get("/{patient_id}/with-preferences")
def get_patient_with_preferences(patient_id: int, db: Session = Depends(get_db)):
    """Get patient data along with their preferences"""
    return patient_service.get_patient_with_preferences(db, patient_id)


@router.delete("/{patient_id}/preferences")
def clear_patient_preferences(patient_id: int, db: Session = Depends(get_db)):
    """Clear patient preferences (reset memory)"""
    memory = patient_memory_service.get_patient_memory(db, patient_id)
    if memory:
        db.delete(memory)
        db.commit()
        return {"message": "Patient preferences cleared successfully"}
    else:
        return {"message": "No preferences found for this patient"}


@router.get("/performance/stats")
def get_performance_stats(hours: int = 24):
    """Get performance statistics for the last N hours"""
    from services.performance_monitor import PerformanceMonitor
    return PerformanceMonitor.get_performance_stats(hours)