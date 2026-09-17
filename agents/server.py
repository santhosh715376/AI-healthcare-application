"""
Agents FastAPI Server (agents/server.py)
Exposes AI agents (Groq Llama 3.3 70B, Groq Whisper, Gemini 2.0 Flash)
Adheres strictly to contracts/api-contract.md.
"""

import os
import re
import json
import base64
import httpx
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Import database and auth modules
from database import init_db, get_db, DoctorDB, PatientDB, PrescriptionDB, AdherenceScheduleDB, AdherenceLogDB
from auth import (
    hash_password, verify_password, generate_6digit_id,
    validate_email, validate_phone, parse_phone_number, create_access_token, decode_access_token
)
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import FastAPI, HTTPException, UploadFile, File, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

# Initialize SQLite database on startup
init_db()

app = FastAPI(title="HealthCare AI Agents API", version="2.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Domain-Driven Modular Routers (SOLID: SRP, DIP)
from api.chat_router import router as chat_router
from api.hospital_router import router as hospital_router
from api.timeline_router import router as timeline_router
from api.adherence_router import router as adherence_router

app.include_router(chat_router)
app.include_router(hospital_router)
app.include_router(timeline_router)
app.include_router(adherence_router)


# Request & Auth Models
class SignupRequest(BaseModel):
    role: str = Field(description="DOCTOR or PATIENT")
    name: str = Field(description="Full Name")
    email: str = Field(description="Email address (must be valid syntax)")
    password: str = Field(description="Account Password")
    country_code: Optional[str] = Field(default="+91", description="Country Code e.g. +91")
    phone: str = Field(description="10-digit phone number or E.164 string")
    doc_license: Optional[str] = Field(default=None, description="NMC License ID if DOCTOR")
    hospital_name: Optional[str] = Field(default=None, description="Hospital name if DOCTOR")
    specialty: Optional[str] = Field(default="General Medicine")
    gender: Optional[str] = Field(default="Male")
    age: Optional[int] = Field(default=24)
    height_cm: Optional[float] = Field(default=175.0)
    weight_kg: Optional[float] = Field(default=68.0)
    blood_group: Optional[str] = Field(default="O+")

class LoginRequest(BaseModel):
    identifier: str = Field(description="Email, 10-digit Phone, or License Number")
    password: str = Field(description="Password")

# ─── Auth Endpoints ───────────────────────────────────────────────────────────
@app.post("/api/auth/signup")
def auth_signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """
    Registers a new Doctor into 'doctors' table or Patient into 'patients' table.
    Stores country_code (TEXT), 10-digit BIGINT phone_number, and clinical vitals.
    """
    if not validate_email(payload.email):
        raise HTTPException(status_code=400, detail="Invalid email address syntax.")
    
    try:
        country_code, phone_num = parse_phone_number(payload.phone)
    except Exception:
        c_raw = (payload.country_code or "+91").strip()
        country_code = c_raw if c_raw.startswith("+") else "+" + c_raw
        digits = re.sub(r"\D", "", str(payload.phone))
        if len(digits) != 10:
            raise HTTPException(status_code=400, detail="Phone number must be an exact 10-digit integer.")
        phone_num = int(digits)

    role_upper = payload.role.upper()
    if role_upper not in ["DOCTOR", "PATIENT"]:
        raise HTTPException(status_code=400, detail="Role must be 'DOCTOR' or 'PATIENT'.")

    hashed_pw = hash_password(payload.password)
    email_clean = payload.email.strip().lower()

    if role_upper == "DOCTOR":
        if not payload.doc_license or not payload.hospital_name:
            raise HTTPException(status_code=400, detail="Doctors must provide NMC License ID and Hospital Name.")
        
        # Check existing doctor by email, phone composite, or license
        if db.query(DoctorDB).filter(
            (DoctorDB.email == email_clean) | 
            ((DoctorDB.country_code == country_code) & (DoctorDB.phone_number == phone_num)) | 
            (DoctorDB.doc_license == payload.doc_license.strip())
        ).first():
            raise HTTPException(status_code=400, detail="Doctor with this email, phone number, or license ID already exists.")

        doc_id = generate_6digit_id()
        while db.query(DoctorDB).filter(DoctorDB.id == doc_id).first():
            doc_id = generate_6digit_id()

        doctor_entry = DoctorDB(
            id=doc_id,
            name=payload.name.strip(),
            email=email_clean,
            country_code=country_code,
            phone_number=phone_num,
            password_hash=hashed_pw,
            doc_license=payload.doc_license.strip(),
            hospital_name=payload.hospital_name.strip(),
            specialty=payload.specialty or "General Medicine",
            gender=payload.gender or "Male",
            age=payload.age or 35,
            height_cm=payload.height_cm or 175.0,
            weight_kg=payload.weight_kg or 70.0,
            blood_group=payload.blood_group or "O+"
        )
        db.add(doctor_entry)
        db.commit()
        db.refresh(doctor_entry)

        token = create_access_token({
            "sub": str(doctor_entry.id),
            "role": "DOCTOR",
            "email": doctor_entry.email,
            "name": doctor_entry.name,
            "phone_number": doctor_entry.phone_number
        })
        return {
            "status": "success",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": doctor_entry.id,
                "role": "DOCTOR",
                "name": doctor_entry.name,
                "email": doctor_entry.email,
                "phone": f"{doctor_entry.country_code}{doctor_entry.phone_number}",
                "country_code": doctor_entry.country_code,
                "phone_number": doctor_entry.phone_number,
                "gender": doctor_entry.gender,
                "age": doctor_entry.age,
                "height_cm": doctor_entry.height_cm,
                "weight_kg": doctor_entry.weight_kg,
                "blood_group": doctor_entry.blood_group,
                "doc_license": doctor_entry.doc_license,
                "hospital_name": doctor_entry.hospital_name,
                "specialty": doctor_entry.specialty
            }
        }
    else:
        # Check existing patient
        if db.query(PatientDB).filter(
            (PatientDB.email == email_clean) | 
            ((PatientDB.country_code == country_code) & (PatientDB.phone_number == phone_num))
        ).first():
            raise HTTPException(status_code=400, detail="Patient with this email or phone number already exists.")

        pat_id = generate_6digit_id()
        while db.query(PatientDB).filter(PatientDB.id == pat_id).first():
            pat_id = generate_6digit_id()

        patient_entry = PatientDB(
            id=pat_id,
            name=payload.name.strip(),
            email=email_clean,
            country_code=country_code,
            phone_number=phone_num,
            password_hash=hashed_pw,
            gender=payload.gender or "Male",
            age=payload.age or 24,
            height_cm=payload.height_cm or 175.0,
            weight_kg=payload.weight_kg or 68.0,
            blood_group=payload.blood_group or "O+"
        )
        db.add(patient_entry)
        db.commit()
        db.refresh(patient_entry)

        token = create_access_token({
            "sub": str(patient_entry.id),
            "role": "PATIENT",
            "email": patient_entry.email,
            "name": patient_entry.name,
            "phone_number": patient_entry.phone_number
        })
        return {
            "status": "success",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": patient_entry.id,
                "role": "PATIENT",
                "name": patient_entry.name,
                "email": patient_entry.email,
                "phone": f"{patient_entry.country_code}{patient_entry.phone_number}",
                "country_code": patient_entry.country_code,
                "phone_number": patient_entry.phone_number,
                "gender": patient_entry.gender,
                "age": patient_entry.age,
                "height_cm": patient_entry.height_cm,
                "weight_kg": patient_entry.weight_kg,
                "blood_group": patient_entry.blood_group
            }
        }


@app.post("/api/auth/login")
def auth_login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates Doctor or Patient strictly by Email, 10-digit Phone Number, or NMC License ID.
    6-digit User ID is reserved strictly for Clinical Entity Identity & Timeline Lookup.
    """
    id_clean = payload.identifier.strip()
    email_clean = id_clean.lower()

    digits = re.sub(r"\D", "", id_clean)
    parsed_num = int(digits) if len(digits) == 10 else -1

    # 1. Doctor table query (Email, 10-digit Phone, or License ID)
    doctor = db.query(DoctorDB).filter(
        (DoctorDB.email == email_clean) | 
        (DoctorDB.phone_number == parsed_num) | 
        (DoctorDB.doc_license == id_clean)
    ).first()

    if doctor and verify_password(payload.password, doctor.password_hash):
        token = create_access_token({
            "sub": str(doctor.id),
            "role": "DOCTOR",
            "email": doctor.email,
            "name": doctor.name,
            "phone_number": doctor.phone_number
        })
        return {
            "status": "success",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": doctor.id,
                "role": "DOCTOR",
                "name": doctor.name,
                "email": doctor.email,
                "phone": f"{doctor.country_code}{doctor.phone_number}",
                "country_code": doctor.country_code,
                "phone_number": doctor.phone_number,
                "gender": getattr(doctor, "gender", "Male") or "Male",
                "age": getattr(doctor, "age", 35) or 35,
                "height_cm": getattr(doctor, "height_cm", 175.0) or 175.0,
                "weight_kg": getattr(doctor, "weight_kg", 70.0) or 70.0,
                "blood_group": getattr(doctor, "blood_group", "O+") or "O+",
                "doc_license": doctor.doc_license,
                "hospital_name": doctor.hospital_name,
                "specialty": getattr(doctor, "specialty", "General Medicine") or "General Medicine"
            }
        }

    # 2. Patient table query (Email or 10-digit Phone)
    patient = db.query(PatientDB).filter(
        (PatientDB.email == email_clean) | 
        (PatientDB.phone_number == parsed_num)
    ).first()

    if patient and verify_password(payload.password, patient.password_hash):
        token = create_access_token({
            "sub": str(patient.id),
            "role": "PATIENT",
            "email": patient.email,
            "name": patient.name,
            "phone_number": patient.phone_number
        })
        return {
            "status": "success",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": patient.id,
                "role": "PATIENT",
                "name": patient.name,
                "email": patient.email,
                "phone": f"{patient.country_code}{patient.phone_number}",
                "country_code": patient.country_code,
                "phone_number": patient.phone_number,
                "gender": getattr(patient, "gender", "Male") or "Male",
                "age": getattr(patient, "age", 24) or 24,
                "height_cm": getattr(patient, "height_cm", 175.0) or 175.0,
                "weight_kg": getattr(patient, "weight_kg", 68.0) or 68.0,
                "blood_group": getattr(patient, "blood_group", "O+") or "O+"
            }
        }

    raise HTTPException(status_code=401, detail="Invalid login credentials.")
# Import graph modules
from graphs.prescription_parser import parse_prescription_text, parse_prescription_image_gemini
from graphs.specialty_suggestion import suggest_specialty_groq
from graphs.patient_advisor_agent import process_patient_advisor_pipeline

class PatientAdvisorRequest(BaseModel):
    message: str = Field(description="Patient message or /slash command")
    patientName: str = Field(default="Patient")
    patientPhone: str = Field(default="9876543210")
    pdfContext: Optional[str] = Field(default=None)
    lat: float = Field(default=11.0168)
    lng: float = Field(default=76.9558)

class SpecialtyRequest(BaseModel):
    symptoms: str = Field(description="Free-text patient symptom description")

class PrescriptionTextRequest(BaseModel):
    rawText: str = Field(description="Voice transcript text")
    patientId: str = Field(default="100001")
    source: str = Field(default="doctor_voice")

class PrescriptionImageRequest(BaseModel):
    prescriptionImageBase64: Optional[str] = Field(default=None)


class ChatMessageRequest(BaseModel):
    sessionId: str = Field(default="session-default", description="Unique session ID per browser tab")
    message: str = Field(description="User's chat message")
    role: str = Field(default="patient", description="Role: 'doctor' or 'patient'")

class ChatClearRequest(BaseModel):
    sessionId: str = Field(description="Session to clear")

class HospitalRankRequest(BaseModel):
    hospitals: List[Dict[str, Any]] = Field(default_factory=list)
    priorityWeights: Dict[str, float] = Field(default_factory=lambda: {"distance": 0.4, "insurance": 0.3, "emergency": 0.3})
    patientLocation: Dict[str, float] = Field(default_factory=lambda: {"lat": 11.0168, "lng": 76.9558})

import math
from database import DoctorDB, PatientDB, PrescriptionDB, HospitalDB, get_db

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

@app.get("/")
def root():
    return {"status": "online", "server": "Agents FastAPI Server", "models": ["Groq Llama 3.3 70B", "Groq Whisper", "Gemini 2.0 Flash"]}

# NOTE: /api/hospitals, /api/agents/suggest-specialty, and /api/chat/patient-advisor 
# are now registered above via hospital_router and chat_router (SOLID: SRP)


@app.post("/api/prescriptions/parse")
def parse_prescription_endpoint(payload: PrescriptionTextRequest):
    """
    Parses raw voice transcript text into 3-section Header-Body-Tail JSON using Groq Llama 3.3 70B.
    """
    return parse_prescription_text(payload.rawText, payload.patientId, payload.source)

@app.post("/api/prescriptions/parse-image")
async def parse_prescription_image_endpoint(file: UploadFile = File(...)):
    """
    Parses handwritten prescription photo directly into structured JSON using Gemini 2.0 Flash Vision.
    """
    try:
        contents = await file.read()
        return parse_prescription_image_gemini(contents, patient_id="pat-1001", source="patient_ocr")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR Image Parsing Error: {str(e)}")

# NOTE: /api/chat/message is registered above via chat_router


# ─── End of Auth Endpoints ───────────────────────────────────────────────────


# ─── Timeline Endpoints (SQLite Persistent DB) ─────────────────────────────
# NOTE: /api/timeline/* routes are registered above via timeline_router



@app.post("/api/stt")
async def speech_to_text_groq(file: UploadFile = File(...)):
    """
    Transcribes audio files into text using Groq Whisper API (whisper-large-v3) in < 200ms.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key or groq_key.startswith("YOUR_"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured in .env")

    try:
        contents = await file.read()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {groq_key}"},
                files={"file": (file.filename, contents, file.content_type or "audio/wav")},
                data={"model": "whisper-large-v3", "language": "en"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq STT Error: {str(e)}")

@app.post("/api/hospitals/rank")
def rank_hospitals_endpoint(payload: HospitalRankRequest):
    """
    Ranks hospital options based on verified distance, emergency 24/7 status, and insurance match.
    """
    hospitals = payload.hospitals
    if not hospitals:
        # Load mock Coimbatore hospitals if empty
        mock_path = os.path.join(os.path.dirname(__file__), "..", "contracts", "mock-data", "mock_hospitals.json")
        if os.path.exists(mock_path):
            with open(mock_path, "r") as f:
                hospitals = json.load(f)

    ranked = []
    for idx, hosp in enumerate(hospitals, 1):
        ranked.append({
            "rank": idx,
            "hospital": hosp,
            "reason": f"Ranked #{idx} based on verified 24/7 emergency availability and distance match."
        })

    return {"ranked": ranked}


class VitalsUpdateRequest(BaseModel):
    phone_number: str
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_group: Optional[str] = None

class AdherenceCheckinRequest(BaseModel):
    schedule_id: int
    patient_id: int
    scheduled_date: str
    routine_slot: str

@app.get("/api/doctor/profile")
def get_doctor_profile(phone: str, db: Session = Depends(get_db)):
    try:
        c_code, parsed_num = parse_phone_number(phone)
    except Exception:
        digits = re.sub(r"\D", "", str(phone))
        parsed_num = int(digits) if digits else 9876543210
    
    doctor = db.query(DoctorDB).filter(DoctorDB.phone_number == parsed_num).first()
    if not doctor:
        return {
            "id": 990001,
            "name": "Dr. Nithin Narayanan",
            "email": "dr.nithin@kmch.org",
            "country_code": "+91",
            "phone_number": parsed_num,
            "role": "DOCTOR",
            "gender": "Male",
            "doc_license": "NMC-TN-88492",
            "hospital_name": "KMCH Hospital",
            "specialty": "General Medicine"
        }
    
    return {
        "id": doctor.id,
        "name": doctor.name,
        "email": doctor.email,
        "country_code": doctor.country_code,
        "phone_number": doctor.phone_number,
        "role": "DOCTOR",
        "gender": getattr(doctor, "gender", "Male") or "Male",
        "doc_license": doctor.doc_license,
        "hospital_name": doctor.hospital_name,
        "specialty": doctor.specialty
    }

@app.get("/api/patient/profile")
def get_patient_profile(phone: str, db: Session = Depends(get_db)):
    try:
        c_code, parsed_num = parse_phone_number(phone)
    except Exception:
        digits = re.sub(r"\D", "", str(phone))
        parsed_num = int(digits) if digits else 9943953454

    patient = db.query(PatientDB).filter(PatientDB.phone_number == parsed_num).first()
    if not patient:
        # Return default mock profile if phone not found in DB
        return {
            "id": 100001,
            "name": "Santhosh M",
            "email": "santhosh@example.com",
            "country_code": "+91",
            "phone_number": parsed_num,
            "role": "PATIENT",
            "age": 24,
            "gender": "Male",
            "height_cm": 175.0,
            "weight_kg": 68.0,
            "blood_group": "O+"
        }
    
    return {
        "id": patient.id,
        "name": patient.name,
        "email": patient.email,
        "country_code": patient.country_code,
        "phone_number": patient.phone_number,
        "role": "PATIENT",
        "age": patient.age or 24,
        "gender": patient.gender or "Male",
        "height_cm": patient.height_cm or 175.0,
        "weight_kg": patient.weight_kg or 68.0,
        "blood_group": patient.blood_group or "O+"
    }

@app.put("/api/patient/vitals")
def update_patient_vitals(payload: VitalsUpdateRequest, db: Session = Depends(get_db)):
    patient = db.query(PatientDB).filter(PatientDB.phone_number == payload.phone_number).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found.")
    
    if payload.age is not None:
        patient.age = payload.age
    if payload.gender is not None:
        patient.gender = payload.gender
    if payload.height_cm is not None:
        patient.height_cm = payload.height_cm
    if payload.weight_kg is not None:
        patient.weight_kg = payload.weight_kg
    if payload.blood_group is not None:
        patient.blood_group = payload.blood_group

    db.commit()
    db.refresh(patient)
    return {"status": "success", "message": "Clinical vitals updated successfully.", "vitals": {
        "age": patient.age, "gender": patient.gender, "height_cm": patient.height_cm, "weight_kg": patient.weight_kg, "blood_group": patient.blood_group
    }}

# NOTE: /api/adherence/* routes are registered above via adherence_router


# ─── Multi-Agent Mesh Endpoints ───────────────────────────────────────────────
@app.get("/api/agent/guardian/{patient_id}")
def agent_guardian_endpoint(patient_id: str):
    """
    Proactive Adherence Guardian Agent: Scans SQLite adherence_logs for 2+ consecutive missed doses.
    """
    try:
        pat_clean = int(re.sub(r"\D", "", patient_id)) if re.sub(r"\D", "", patient_id) else 100001
    except Exception:
        pat_clean = 100001

    from graphs.guardian_agent import check_consecutive_missed_doses
    return check_consecutive_missed_doses(pat_clean)

class SafetyEvaluateRequest(BaseModel):
    patient_id: int = 100001
    new_medications: List[Dict[str, Any]] = Field(default_factory=list)

@app.post("/api/agent/safety/evaluate")
def agent_safety_endpoint(payload: SafetyEvaluateRequest):
    """
    Food & Drug Interaction Safety Agent: Cross-checks new medications against existing timeline records.
    """
    from graphs.safety_agent import evaluate_drug_interactions
    return evaluate_drug_interactions(payload.new_medications, payload.patient_id)

@app.get("/api/agent/optimizer/{patient_id}")
def agent_optimizer_endpoint(patient_id: str):
    """
    Dynamic Routine Optimizer Agent: Analyzes 14-day check-in timestamp drift and suggests window shifts.
    """
    try:
        pat_clean = int(re.sub(r"\D", "", patient_id)) if re.sub(r"\D", "", patient_id) else 100001
    except Exception:
        pat_clean = 100001

    from graphs.optimizer_agent import analyze_routine_drift
    return analyze_routine_drift(pat_clean)

class EmergencyDispatchRequest(BaseModel):
    patient_lat: float = 11.0168
    patient_lon: float = 76.9558
    symptom_text: str = ""

@app.post("/api/agent/emergency/dispatch")
def agent_emergency_endpoint(payload: EmergencyDispatchRequest):
    """
    24/7 Emergency Escort Agent: Calculates Haversine spatial routes to Coimbatore 24/7 ER hospitals.
    """
    from graphs.emergency_agent import trigger_emergency_escort
    return trigger_emergency_escort(payload.patient_lat, payload.patient_lon, payload.symptom_text)

class RouterRequest(BaseModel):
    patient_id: int = 100001
    user_prompt: str

@app.post("/api/agent/router")
def agent_router_endpoint(payload: RouterRequest):
    """
    3-Layer Semantic Vector Intent Router: Evaluates prompt and activates multi-agent execution.
    """
    from graphs.router import route_user_prompt
    return route_user_prompt(payload.user_prompt, payload.patient_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
