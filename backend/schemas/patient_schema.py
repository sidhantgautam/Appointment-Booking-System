from pydantic import BaseModel

class PatientCreate(BaseModel):
    name: str
    language: str = "English"

class PatientResponse(BaseModel):
    id: int
    name: str
    language: str

    class Config:
        from_attributes = True