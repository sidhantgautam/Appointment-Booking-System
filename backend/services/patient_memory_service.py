"""
Patient Memory Service
Manages persistent patient preferences and interaction history
"""

from sqlalchemy.orm import Session
from datetime import datetime
import models
import re


def get_patient_memory(db: Session, patient_id: int):
    """Get patient memory/preferences"""
    return db.query(models.PatientMemory).filter(
        models.PatientMemory.patient_id == patient_id
    ).first()


def create_patient_memory(db: Session, patient_id: int, **preferences):
    """Create new patient memory record"""
    memory = models.PatientMemory(
        patient_id=patient_id,
        preferred_language=preferences.get("preferred_language", "en"),
        preferred_doctor_id=preferences.get("preferred_doctor_id"),
        preferred_doctor_name=preferences.get("preferred_doctor_name"),
        preferred_specialization=preferences.get("preferred_specialization"),
        preferred_time_slot=preferences.get("preferred_time_slot"),
        preferred_day_type=preferences.get("preferred_day_type"),
        interaction_count=1,
        notes=preferences.get("notes")
    )
    
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def update_patient_memory(db: Session, patient_id: int, **preferences):
    """Update existing patient memory"""
    memory = get_patient_memory(db, patient_id)
    
    if not memory:
        return create_patient_memory(db, patient_id, **preferences)
    
    # Update preferences if provided
    if "preferred_language" in preferences:
        memory.preferred_language = preferences["preferred_language"]
    if "preferred_doctor_id" in preferences:
        memory.preferred_doctor_id = preferences["preferred_doctor_id"]
    if "preferred_doctor_name" in preferences:
        memory.preferred_doctor_name = preferences["preferred_doctor_name"]
    if "preferred_specialization" in preferences:
        memory.preferred_specialization = preferences["preferred_specialization"]
    if "preferred_time_slot" in preferences:
        memory.preferred_time_slot = preferences["preferred_time_slot"]
    if "preferred_day_type" in preferences:
        memory.preferred_day_type = preferences["preferred_day_type"]
    if "notes" in preferences:
        memory.notes = preferences["notes"]
    
    # Update interaction tracking
    memory.interaction_count += 1
    memory.last_interaction = datetime.now()
    memory.updated_at = datetime.now()
    
    db.commit()
    db.refresh(memory)
    return memory


def extract_preferences_from_interaction(session_memory: dict, agent_result: dict):
    """
    Extract preferences from a successful interaction
    Returns dict of preferences to store
    """
    preferences = {}
    
    # Extract language preference
    if "detected_language" in session_memory:
        preferences["preferred_language"] = session_memory["detected_language"]
    
    # Extract doctor preference
    if "doctor_name" in session_memory:
        preferences["preferred_doctor_name"] = session_memory["doctor_name"]
    
    # Extract specialization preference
    if "specialization" in session_memory:
        preferences["preferred_specialization"] = session_memory["specialization"]
    
    # Extract time preference
    if "time" in session_memory:
        time_str = session_memory["time"]
        preferences["preferred_time_slot"] = time_str
        
        if "date" in session_memory:
            date_str = session_memory["date"].lower()
            if any(day in date_str for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]):
                preferences["preferred_day_type"] = "weekday"
            elif any(day in date_str for day in ["saturday", "sunday"]):
                preferences["preferred_day_type"] = "weekend"
    
    return preferences


def get_patient_preferences_context(db: Session, patient_id: int):
    """
    Get patient preferences formatted for agent context
    Returns dict with preferences and suggestions
    """
    memory = get_patient_memory(db, patient_id)
    
    if not memory:
        return {
            "has_preferences": False,
            "message": f"New patient (ID: {patient_id})"
        }
    
    context = {
        "has_preferences": True,
        "patient_id": patient_id,
        "interaction_count": memory.interaction_count,
        "last_interaction": memory.last_interaction.isoformat() if memory.last_interaction else None,
        "preferences": {}
    }
    
    # Build preferences context
    if memory.preferred_language:
        context["preferences"]["language"] = memory.preferred_language
    
    if memory.preferred_doctor_name:
        context["preferences"]["doctor"] = memory.preferred_doctor_name
    
    if memory.preferred_specialization:
        context["preferences"]["specialization"] = memory.preferred_specialization
    
    if memory.preferred_time_slot:
        context["preferences"]["time_slot"] = memory.preferred_time_slot
    
    if memory.preferred_day_type:
        context["preferences"]["day_type"] = memory.preferred_day_type
    
    # Generate suggestion message
    suggestions = []
    if memory.preferred_doctor_name:
        suggestions.append(f"usual doctor: {memory.preferred_doctor_name}")
    if memory.preferred_time_slot:
        suggestions.append(f"usual time: {memory.preferred_time_slot}")
    if memory.preferred_specialization:
        suggestions.append(f"specialty: {memory.preferred_specialization}")
    
    if suggestions:
        context["suggestion_message"] = f"Based on your history ({', '.join(suggestions)}), would you like to book with the same preferences?"
    
    return context


def apply_preferences_to_session(session_memory: dict, patient_preferences: dict):
    """
    Apply stored patient preferences to current session memory
    Only applies if not already set in session
    """
    if not patient_preferences.get("has_preferences"):
        return session_memory
    
    prefs = patient_preferences.get("preferences", {})
    
    if "doctor" in prefs and "doctor_name" not in session_memory:
        session_memory["doctor_name"] = prefs["doctor"]
    
    if "specialization" in prefs and "specialization" not in session_memory:
        session_memory["specialization"] = prefs["specialization"]
    
    if "time_slot" in prefs and "time" not in session_memory:
        session_memory["time"] = prefs["time_slot"]
    
    # Apply language preference
    if "language" in prefs:
        session_memory["preferred_language"] = prefs["language"]
    
    return session_memory


def get_patient_interaction_history(db: Session, patient_id: int, limit: int = 10):
    """Get recent appointments for this patient"""
    appointments = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id
    ).order_by(models.Appointment.id.desc()).limit(limit).all()
    
    history = []
    for appt in appointments:
        doctor = db.query(models.Doctor).filter(
            models.Doctor.id == appt.doctor_id
        ).first()
        
        history.append({
            "appointment_id": appt.id,
            "doctor_name": doctor.name if doctor else "Unknown",
            "specialization": doctor.specialization if doctor else "Unknown",
            "time": appt.time
        })
    
    return history


def suggest_based_on_history(db: Session, patient_id: int):
    """
    Generate smart suggestions based on patient history
    """
    memory = get_patient_memory(db, patient_id)
    history = get_patient_interaction_history(db, patient_id, limit=5)
    
    if not memory and not history:
        return None
    
    suggestions = {
        "type": "smart_suggestions",
        "patient_id": patient_id
    }
    
    # Analyze appointment patterns
    if history:
        # Most frequent doctor
        doctor_counts = {}
        time_patterns = {}
        
        for appt in history:
            doctor = appt["doctor_name"]
            doctor_counts[doctor] = doctor_counts.get(doctor, 0) + 1
            
            # Extract hour from time
            time_str = appt["time"]
            try:
                hour = int(time_str.split(":")[0].split(" ")[-1])
                if hour < 12:
                    time_period = "morning"
                elif hour < 17:
                    time_period = "afternoon"
                else:
                    time_period = "evening"
                time_patterns[time_period] = time_patterns.get(time_period, 0) + 1
            except:
                pass
        
        # Most frequent doctor
        if doctor_counts:
            most_frequent_doctor = max(doctor_counts, key=doctor_counts.get)
            suggestions["frequent_doctor"] = {
                "name": most_frequent_doctor,
                "count": doctor_counts[most_frequent_doctor]
            }
        
        # Most frequent time period
        if time_patterns:
            most_frequent_time = max(time_patterns, key=time_patterns.get)
            suggestions["frequent_time_period"] = {
                "period": most_frequent_time,
                "count": time_patterns[most_frequent_time]
            }
    
    # Add stored preferences
    if memory:
        suggestions["stored_preferences"] = {
            "doctor": memory.preferred_doctor_name,
            "time": memory.preferred_time_slot,
            "specialization": memory.preferred_specialization
        }
    
    return suggestions