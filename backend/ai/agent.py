import ollama
import re

from db.db import SessionLocal
from sqlalchemy.orm import Session
from services import appointment_service
from services import patient_service, patient_memory_service
import models

from utils.time_parser import normalize_time
from ai.memory import get_memory, update_memory, clear_memory, add_to_conversation_history, get_recent_context


def _return_with_history(session_id: str, response: dict):
    message = response.get("message") or response.get("error") or str(response.get("action", ""))
    if message:
        add_to_conversation_history(session_id, "agent", message)
    return response


def _load_patient_preferences(db: Session, patient_id: int, session_id: str):
    if not patient_id:
        return None
    
    preferences = patient_memory_service.get_patient_preferences_context(db, patient_id)
    
    if preferences.get("has_preferences"):
        session_memory = get_memory(session_id)
        updated_memory = patient_memory_service.apply_preferences_to_session(
            session_memory, preferences
        )
        
        for key, value in updated_memory.items():
            if key not in session_memory:
                update_memory(session_id, key, value)
    
    return preferences


def _save_patient_preferences(db: Session, patient_id: int, session_id: str, agent_result: dict):
    if not patient_id:
        return
    
    if agent_result.get("action") == "book_appointment":
        session_memory = get_memory(session_id)
        preferences = patient_memory_service.extract_preferences_from_interaction(
            session_memory, agent_result
        )
        
        if preferences:
            patient_memory_service.update_patient_memory(db, patient_id, **preferences)


def run_agent(user_text: str, session_id: str = "default"):

    add_to_conversation_history(session_id, "user", user_text)

    memory = get_memory(session_id)
    db = SessionLocal()

    patient_id = memory.get("patient_id")
    patient_preferences = None
    
    if not patient_id:
        patient_match = re.search(r"patient\s*(\d+)", user_text, re.IGNORECASE)
        if patient_match:
            patient_id = int(patient_match.group(1))
            update_memory(session_id, "patient_id", patient_id)
    
    if patient_id:
        patient_preferences = _load_patient_preferences(db, patient_id, session_id)

    date_keywords = ["tomorrow", "today", "monday", "tuesday", "wednesday", 
                     "thursday", "friday", "saturday", "sunday", "next week"]
    
    user_lower = user_text.lower()
    for keyword in date_keywords:
        if keyword in user_lower:
            date_match = re.search(
                r"(tomorrow|today|next\s+\w+|this\s+\w+|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
                user_lower
            )
            if date_match:
                update_memory(session_id, "date", date_match.group())
                break
    
    if not memory.get("date"):
        date_pattern_match = re.search(
            r"(\w+\s+\d{1,2}(?:st|nd|rd|th)?|\d{1,2}(?:st|nd|rd|th)?\s+\w+|\d{1,2}/\d{1,2})",
            user_text,
            re.IGNORECASE
        )
        if date_pattern_match:
            update_memory(session_id, "date", date_pattern_match.group())
    
    memory = get_memory(session_id)

    # Check if user is responding to a booking conflict suggestion
    suggested_time = memory.get("suggested_time")
    if suggested_time and ("yes" in user_text.lower() or "no" in user_text.lower() or "ok" in user_text.lower() or "sure" in user_text.lower()):
        # Force intent to be booking since user is responding to booking conflict
        intent = "book_appointment"
        update_memory(session_id, "intent", intent)
    else:
        intent = memory.get("intent")

    if not intent:
        prompt = f"""
Classify the intent of this request.

Possible intents:
- book_appointment
- cancel_appointment
- reschedule_appointment
- list_doctors
- list_appointments
- delete_all_appointments
- create_patient
- list_patients

Return only the intent name.

Request:
{user_text}
"""

        response = ollama.chat(
            model="phi3:mini",
            options={
                "temperature": 0,
                "num_predict": 20
            },
            messages=[{"role": "user", "content": prompt}]
        )

        intent = response["message"]["content"].strip().lower()

        update_memory(session_id, "intent", intent)

        response = ollama.chat(
            model="phi3:mini",
            options={
                "temperature": 0,
                "num_predict": 20
            },
            messages=[{"role": "user", "content": prompt}]
        )

        intent = response["message"]["content"].strip().lower()

        update_memory(session_id, "intent", intent)

    if "book" in intent:
        # Check if user is confirming a suggested time slot
        memory = get_memory(session_id)
        suggested_time = memory.get("suggested_time")
        
        if suggested_time and ("yes" in user_text.lower() or "ok" in user_text.lower() or "sure" in user_text.lower()):
            # User confirmed the suggested time, book it directly
            patient_id = memory.get("patient_id")
            doctor_name = memory.get("doctor_name")
            
            if patient_id and doctor_name:
                # Find the doctor
                doctor = db.query(models.Doctor).filter(
                    models.Doctor.name.ilike(f"%{doctor_name}%")
                ).first()
                
                if doctor:
                    # Book the suggested time
                    result = appointment_service.book_appointment(
                        db,
                        patient_id=patient_id,
                        doctor_id=doctor.id,
                        time=suggested_time
                    )
                    
                    # Clear memory after booking
                    clear_memory(session_id)
                    
                    if isinstance(result, dict) and "error" in result:
                        return {
                            "action": "booking_conflict",
                            "error": "Sorry, that time slot is no longer available. Please try booking again."
                        }
                    
                    _save_patient_preferences(db, patient_id, session_id, {
                        "action": "book_appointment",
                        "result": result
                    })
                    
                    return {
                        "action": "book_appointment",
                        "result": {
                            "id": result.id,
                            "patient_id": result.patient_id,
                            "doctor_id": result.doctor_id,
                            "time": result.time,
                            "message": f"Appointment booked successfully for patient {result.patient_id} on {result.time}"
                        }
                    }
        
        # Check if user is declining a suggested time slot
        if suggested_time and ("no" in user_text.lower() or "not" in user_text.lower()):
            # Clear the suggested time and ask for a new time
            update_memory(session_id, "suggested_time", None)
            return {"message": "Please provide a different date and time for your appointment."}

        doctor_match = re.search(
            r"dr\.?\s+([a-zA-Z]+)",
            user_text,
            re.IGNORECASE
        )

        specialization_keywords = [
            "cardiologist", "neurologist", "dermatologist", "pediatrician",
            "orthopedic", "psychiatrist", "oncologist", "radiologist",
            "cardiology", "neurology", "dermatology", "pediatrics",
            "orthopedics", "psychiatry", "oncology", "radiology"
        ]
        
        specialization_match = None
        for keyword in specialization_keywords:
            if keyword in user_text.lower():
                specialization_match = keyword
                break

        if doctor_match:
            doctor_name = doctor_match.group(1)
            update_memory(session_id, "doctor_name", doctor_name)
        elif specialization_match:
            update_memory(session_id, "specialization", specialization_match)
        
        memory = get_memory(session_id)
        doctor_name = memory.get("doctor_name")
        specialization = memory.get("specialization")

        if not doctor_name and not specialization and patient_preferences and patient_preferences.get("has_preferences"):
            prefs = patient_preferences.get("preferences", {})
            if "doctor" in prefs:
                suggestion_msg = f"Would you like to book with your usual doctor, {prefs['doctor']}? (yes/no)"
                if "specialization" in prefs:
                    suggestion_msg += f" They specialize in {prefs['specialization']}."
                return {"message": suggestion_msg}

        if not doctor_name and not specialization:
            # Show patient history if available
            if patient_preferences and patient_preferences.get("has_preferences"):
                base_msg = "Which doctor would you like to book an appointment with? (You can specify a name or specialization)"
                if patient_preferences.get("suggestion_message"):
                    return {"message": f"{base_msg}\n\n{patient_preferences['suggestion_message']}"}
                return {"message": base_msg}
            else:
                return {
                    "message": "Which doctor would you like to book an appointment with? (You can specify a name or specialization)"
                }

        # Find doctor by name or specialization
        if doctor_name:
            doctor = db.query(models.Doctor).filter(
                models.Doctor.name.ilike(f"%{doctor_name}%")
            ).first()
        else:
            # Search by specialization
            doctors = appointment_service.find_doctor_by_specialization(db, specialization)
            if not doctors:
                return {"error": f"No doctors found with specialization: {specialization}"}
            
            if len(doctors) == 1:
                doctor = doctors[0]
                update_memory(session_id, "doctor_name", doctor.name)
            else:
                doctor_list = [f"Dr {d.name} ({d.specialization})" for d in doctors]
                return {
                    "message": f"Multiple {specialization}s available: {', '.join(doctor_list)}. Which one would you prefer?"
                }

        if not doctor:
            return {"error": f"Doctor {doctor_name} not found"}

        # patient extraction

        patient_match = re.search(
            r"patient\s*(\d+)",
            user_text,
            re.IGNORECASE
        )

        if patient_match:
            patient_id = int(patient_match.group(1))
            update_memory(session_id, "patient_id", patient_id)
        
        # Refresh memory to get latest values
        memory = get_memory(session_id)
        patient_id = memory.get("patient_id")

        if not patient_id:
            return {"message": "Which patient ID should I use?"}

        patient = db.query(models.Patient).filter(
            models.Patient.id == patient_id
        ).first()

        if not patient:
            # Suggest creating a new patient
            return {
                "message": f"Patient {patient_id} not found. Would you like to create a new patient? Say 'create patient [name]' to add a new patient."
            }

        # date + time extraction

        time_match = re.search(
            r"(\d{1,2}\s*(?:AM|PM|A\.M\.?|P\.M\.?|am|pm|a\.m\.?|p\.m\.?)|\d{1,2}:\d{2}\s*(?:AM|PM|A\.M\.?|P\.M\.?|am|pm|a\.m\.?|p\.m\.?)?|\d{1,2}:\d{2})",
            user_text,
            re.IGNORECASE
        )

        if time_match:
            time_str = time_match.group().strip()
            time_str = time_str.replace("A.M.", "AM").replace("P.M.", "PM")
            time_str = time_str.replace("A.M", "AM").replace("P.M", "PM")
            time_str = time_str.replace("a.m.", "am").replace("p.m.", "pm")
            time_str = time_str.replace("a.m", "am").replace("p.m", "pm")
            update_memory(session_id, "time", time_str)

        # refresh memory after updates
        memory = get_memory(session_id)

        date_part = memory.get("date")
        time_part = memory.get("time")

        # ask missing pieces
        if not date_part:
            return {"message": "Which day should I schedule the appointment?"}

        if not time_part:
            return {"message": "What time should I schedule the appointment?"}

        combined_time = f"{date_part} {time_part}"

        normalized_time = normalize_time(combined_time)

        # booking

        result = appointment_service.book_appointment(
            db,
            patient_id=patient_id,
            doctor_id=doctor.id,
            time=normalized_time
        )

        if isinstance(result, dict) and "error" in result:
            # Find next available slot
            next_slot = appointment_service.find_next_available_slot(
                db, doctor.id, normalized_time
            )
            
            if next_slot:
                from datetime import datetime
                next_dt = datetime.strptime(next_slot, "%Y-%m-%d %H:%M")
                formatted_time = next_dt.strftime("%B %d at %I:%M %p")
                
                update_memory(session_id, "suggested_time", next_slot)
                
                return {
                    "action": "booking_conflict",
                    "message": f"That time slot is already booked. The next available slot is {formatted_time}. Would you like to book that instead? (yes/no)",
                    "result": {
                        "suggested_time": next_slot,
                        "message": f"That time slot is already booked. The next available slot is {formatted_time}. Would you like to book that instead? (yes/no)"
                    }
                }
            else:
                clear_memory(session_id)
                return {
                    "action": "booking_conflict",
                    "error": "No available slots found in the next 8 hours. Please try a different day."
                }

        # clear memory after success
        clear_memory(session_id)

        _save_patient_preferences(db, patient_id, session_id, {
            "action": "book_appointment",
            "result": result
        })

        # safe response handling
        if isinstance(result, dict):
            return {
                "action": "book_appointment",
                "result": result
            }

        return {
            "action": "book_appointment",
            "result": {
                "id": result.id,
                "patient_id": result.patient_id,
                "doctor_id": result.doctor_id,
                "time": result.time,
                "message": f"Appointment booked successfully for patient {result.patient_id} on {result.time}"
            }
        }

    # CANCEL APPOINTMENT
    elif "cancel" in intent:
        
        # Extract doctor name
        doctor_match = re.search(
            r"dr\.?\s+([a-zA-Z]+)",
            user_text,
            re.IGNORECASE
        )

        if doctor_match:
            doctor_name = doctor_match.group(1)
            update_memory(session_id, "doctor_name", doctor_name)
        
        memory = get_memory(session_id)
        doctor_name = memory.get("doctor_name")
        
        # Extract patient ID
        patient_match = re.search(
            r"patient\s*(\d+)",
            user_text,
            re.IGNORECASE
        )

        if patient_match:
            patient_id = int(patient_match.group(1))
            update_memory(session_id, "patient_id", patient_id)
        
        memory = get_memory(session_id)
        patient_id = memory.get("patient_id")
        
        # Get date if provided
        date_part = memory.get("date")
        
        # Ask for missing information
        if not patient_id:
            return {"message": "Which patient ID should I use for cancellation?"}
        
        if not doctor_name:
            return {"message": "Which doctor's appointment would you like to cancel?"}
        
        # Find the doctor
        doctor = db.query(models.Doctor).filter(
            models.Doctor.name.ilike(f"%{doctor_name}%")
        ).first()

        if not doctor:
            clear_memory(session_id)
            return {"error": f"Doctor {doctor_name} not found"}
        
        # Find appointments matching criteria
        normalized_time = None
        if date_part:
            # If time is also provided, use it
            time_part = memory.get("time")
            if time_part:
                combined_time = f"{date_part} {time_part}"
                normalized_time = normalize_time(combined_time)
            else:
                normalized_time = normalize_time(date_part)
        
        appointments = appointment_service.find_appointment_by_criteria(
            db,
            patient_id=patient_id,
            doctor_id=doctor.id,
            time=normalized_time if normalized_time else None
        )
        
        if not appointments:
            clear_memory(session_id)
            return {"error": "No matching appointment found"}
        
        if len(appointments) > 1 and not normalized_time:
            appt_list = [f"ID {a.id}: {a.time}" for a in appointments]
            return {
                "message": f"Multiple appointments found: {', '.join(appt_list)}. Please specify the date/time or appointment ID."
            }
        
        # Cancel the appointment
        appointment = appointments[0]
        result = appointment_service.cancel_appointment(db, appointment.id)
        
        clear_memory(session_id)
        
        return {
            "action": "cancel_appointment",
            "result": {
                "appointment_id": appointment.id,
                "message": f"Appointment with Dr {doctor_name} on {appointment.time} has been cancelled"
            }
        }

    # RESCHEDULE APPOINTMENT
    elif "reschedule" in intent:
        
        # Extract doctor name
        doctor_match = re.search(
            r"dr\.?\s+([a-zA-Z]+)",
            user_text,
            re.IGNORECASE
        )

        if doctor_match:
            doctor_name = doctor_match.group(1)
            update_memory(session_id, "doctor_name", doctor_name)
        
        memory = get_memory(session_id)
        doctor_name = memory.get("doctor_name")
        
        # Extract patient ID
        patient_match = re.search(
            r"patient\s*(\d+)",
            user_text,
            re.IGNORECASE
        )

        if patient_match:
            patient_id = int(patient_match.group(1))
            update_memory(session_id, "patient_id", patient_id)
        
        memory = get_memory(session_id)
        patient_id = memory.get("patient_id")
        
        # Extract time
        time_match = re.search(
            r"(\d{1,2}\s*(?:AM|PM|A\.M\.?|P\.M\.?|am|pm|a\.m\.?|p\.m\.?)|\d{1,2}:\d{2}\s*(?:AM|PM|A\.M\.?|P\.M\.?|am|pm|a\.m\.?|p\.m\.?)?|\d{1,2}:\d{2})",
            user_text,
            re.IGNORECASE
        )

        if time_match:
            time_str = time_match.group().strip()
            time_str = time_str.replace("A.M.", "AM").replace("P.M.", "PM")
            time_str = time_str.replace("A.M", "AM").replace("P.M", "PM")
            time_str = time_str.replace("a.m.", "am").replace("p.m.", "pm")
            time_str = time_str.replace("a.m", "am").replace("p.m", "pm")
            update_memory(session_id, "new_time", time_str)
        
        memory = get_memory(session_id)
        date_part = memory.get("date")
        new_time_part = memory.get("new_time")
        
        # Ask for missing information
        if not patient_id:
            return {"message": "Which patient ID should I use for rescheduling?"}
        
        if not doctor_name:
            return {"message": "Which doctor's appointment would you like to reschedule?"}
        
        # Find the doctor
        doctor = db.query(models.Doctor).filter(
            models.Doctor.name.ilike(f"%{doctor_name}%")
        ).first()

        if not doctor:
            clear_memory(session_id)
            return {"error": f"Doctor {doctor_name} not found"}
        
        # Find the appointment to reschedule
        appointments = appointment_service.find_appointment_by_criteria(
            db,
            patient_id=patient_id,
            doctor_id=doctor.id
        )
        
        if not appointments:
            clear_memory(session_id)
            return {"error": "No appointment found to reschedule"}
        
        if len(appointments) > 1:
            appt_list = [f"ID {a.id}: {a.time}" for a in appointments]
            return {
                "message": f"Multiple appointments found: {', '.join(appt_list)}. Please specify which one to reschedule."
            }
        
        appointment = appointments[0]
        
        # Check if new time is provided
        if not date_part or not new_time_part:
            return {"message": "What is the new date and time for the appointment?"}
        
        # Normalize the new time
        combined_time = f"{date_part} {new_time_part}"
        normalized_new_time = normalize_time(combined_time)
        
        # Reschedule
        result = appointment_service.reschedule_appointment(
            db,
            appointment.id,
            normalized_new_time
        )
        
        clear_memory(session_id)
        
        if isinstance(result, dict) and "error" in result:
            return {
                "action": "reschedule_appointment",
                "result": result
            }
        
        return {
            "action": "reschedule_appointment",
            "result": {
                "appointment_id": result.id,
                "old_time": appointment.time,
                "new_time": result.time,
                "message": f"Appointment rescheduled from {appointment.time} to {result.time}"
            }
        }

    # LIST DOCTORS
    elif "list" in intent and "doctor" in intent:
        doctors = appointment_service.get_doctors_with_details(db)
        
        if not doctors:
            return {
                "action": "list_doctors",
                "result": {
                    "message": "No doctors available",
                    "doctors": []
                }
            }
        
        # Format doctor list for display
        doctor_list = []
        for doc in doctors:
            doctor_list.append(
                f"Dr {doc['name']} - {doc['specialization']} ({doc['total_appointments']} appointments)"
            )
        
        return {
            "action": "list_doctors",
            "result": {
                "message": f"Available doctors ({len(doctors)}):",
                "doctors": doctors,
                "formatted_list": doctor_list
            }
        }

    # LIST APPOINTMENTS
    elif "list" in intent and "appointment" in intent:
        # Extract patient ID
        patient_match = re.search(
            r"patient\s*(\d+)",
            user_text,
            re.IGNORECASE
        )

        if patient_match:
            patient_id = int(patient_match.group(1))
            update_memory(session_id, "patient_id", patient_id)
        
        memory = get_memory(session_id)
        patient_id = memory.get("patient_id")
        
        if not patient_id:
            return {"message": "Which patient ID should I use to show appointments?"}
        
        # Get appointments for patient
        appointments = appointment_service.get_appointments_by_patient(db, patient_id)
        
        if not appointments:
            clear_memory(session_id)
            return {
                "action": "list_appointments",
                "result": {
                    "message": f"No appointments found for patient {patient_id}",
                    "appointments": []
                }
            }
        
        # Format appointment list
        appt_list = []
        for appt in appointments:
            appt_list.append(
                f"{appt['time']} - Dr {appt['doctor_name']} ({appt['specialization']})"
            )
        
        clear_memory(session_id)
        
        return {
            "action": "list_appointments",
            "result": {
                "message": f"Found {len(appointments)} appointment(s) for patient {patient_id}:",
                "appointments": appointments,
                "formatted_list": appt_list
            }
        }

    # DELETE ALL APPOINTMENTS
    elif "delete" in intent and "all" in intent:
        # Extract patient ID
        patient_match = re.search(
            r"patient\s*(\d+)",
            user_text,
            re.IGNORECASE
        )

        if patient_match:
            patient_id = int(patient_match.group(1))
            update_memory(session_id, "patient_id", patient_id)
        
        memory = get_memory(session_id)
        patient_id = memory.get("patient_id")
        
        if not patient_id:
            return {"message": "Which patient ID should I use to delete all appointments?"}
        
        # Get all appointments for patient first
        appointments = appointment_service.get_appointments_by_patient(db, patient_id)
        
        if not appointments:
            clear_memory(session_id)
            return {
                "action": "delete_all_appointments",
                "result": {
                    "message": f"No appointments found for patient {patient_id} to delete",
                    "deleted_count": 0
                }
            }
        
        # Delete all appointments
        deleted_count = 0
        for appt in appointments:
            try:
                appointment_service.cancel_appointment(db, appt['id'])
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting appointment {appt['id']}: {e}")
        
        clear_memory(session_id)
        
        return {
            "action": "delete_all_appointments",
            "result": {
                "message": f"Successfully deleted {deleted_count} appointment(s) for patient {patient_id}",
                "deleted_count": deleted_count,
                "patient_id": patient_id
            }
        }

    # CREATE PATIENT
    elif "create" in intent and "patient" in intent:
        # Extract patient name
        name_patterns = [
            r"create\s+(?:a\s+)?(?:new\s+)?patient\s+(?:named\s+)?([a-zA-Z]+)",
            r"add\s+(?:a\s+)?(?:new\s+)?patient\s+(?:named\s+)?([a-zA-Z]+)",
            r"new\s+patient\s+(?:named\s+)?([a-zA-Z]+)",
            r"patient\s+(?:named\s+)?([a-zA-Z]+)"
        ]
        
        patient_name = None
        for pattern in name_patterns:
            name_match = re.search(pattern, user_text, re.IGNORECASE)
            if name_match:
                patient_name = name_match.group(1).strip().title()
                break
        
        if not patient_name:
            return {"message": "What should I name the new patient?"}
        
        # Check if patient with this name already exists
        existing_patients = patient_service.get_all_patients(db)
        for existing in existing_patients:
            if existing.name.lower() == patient_name.lower():
                return {
                    "error": f"Patient named {patient_name} already exists with ID {existing.id}"
                }
        
        # Create the new patient
        try:
            new_patient = patient_service.create_patient(
                db, 
                name=patient_name, 
                language="en"  # Default to English, can be updated later
            )
            
            clear_memory(session_id)
            
            return {
                "action": "create_patient",
                "result": {
                    "id": new_patient.id,
                    "name": new_patient.name,
                    "language": new_patient.language,
                    "message": f"Successfully created patient '{patient_name}' with ID {new_patient.id}"
                }
            }
        except Exception as e:
            return {
                "action": "create_patient",
                "error": f"Failed to create patient: {str(e)}"
            }

    # LIST PATIENTS
    elif "list" in intent and "patient" in intent:
        patients = patient_service.get_all_patients(db)
        
        if not patients:
            return {
                "action": "list_patients",
                "result": {
                    "message": "No patients found in the system",
                    "patients": []
                }
            }
        
        # Format patient list
        patient_list = []
        for patient in patients:
            patient_list.append(f"ID {patient.id}: {patient.name} ({patient.language})")
        
        return {
            "action": "list_patients",
            "result": {
                "message": f"Found {len(patients)} patient(s):",
                "patients": [{"id": p.id, "name": p.name, "language": p.language} for p in patients],
                "formatted_list": patient_list
            }
        }

    return _return_with_history(session_id, {"intent": intent})