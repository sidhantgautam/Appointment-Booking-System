from pydantic import BaseModel

class DoctorCreate(BaseModel):
    name: str
    specialization: str


class DoctorResponse(BaseModel):
    id: int
    name: str
    specialization: str

    class Config:
        from_attributes = True

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    time: str


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    time: str

    class Config:
        from_attributes = True

class RescheduleAppointment(BaseModel):
    appointment_id: int
    new_time: str