from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import patient_routes, appointment_routes, voice_routes, ai_routes, outbound_routes
from db.db import engine

import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Voice AI Clinic Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patient_routes.router)
app.include_router(appointment_routes.router)
app.include_router(voice_routes.router)
app.include_router(ai_routes.router)
app.include_router(outbound_routes.router)

@app.get("/")
def read_root():
    return {"message": "Voice AI Clinic Agent Running"}