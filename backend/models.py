from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from db.db import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    language = Column(String, default="English")

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialization = Column(String)

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    time = Column(String)

class PatientMemory(Base):
    __tablename__ = "patient_memory"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True)
    preferred_language = Column(String, default="en")
    preferred_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    preferred_doctor_name = Column(String, nullable=True)
    preferred_specialization = Column(String, nullable=True)
    preferred_time_slot = Column(String, nullable=True)  # e.g., "10 AM", "morning", "afternoon"
    preferred_day_type = Column(String, nullable=True)   # e.g., "weekday", "weekend"
    interaction_count = Column(Integer, default=0)
    last_interaction = Column(DateTime, default=func.now())
    notes = Column(Text, nullable=True)  # Additional preferences or notes
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())