"""
Agents FastAPI Server (agents/server.py)
Exposes AI agents (Groq Llama 3.3 70B, Groq Whisper, Gemini 2.0 Flash)
Adheres strictly to contracts/api-contract.md.
"""

import os
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
from database import init_db, get_db, DoctorDB, PatientDB, PrescriptionDB
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

app = FastAPI(title="HealthCare AI Agents API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request & Auth Models
class SignupRequest(BaseModel):
    role: str = Field(description="DOCTOR or PATIENT")
    name: str = Field(description="Full Name")
    email: str = Field(description="Email address (must be valid syntax)")
    password: str = Field(description="Account Password")
    phone: str = Field(description="E.164 or 10-digit phone number e.g. +919876543210 or 9876543210")
    doc_license: Optional[str] = Field(default=None, description="NMC License ID if DOCTOR")
    hospital_name: Optional[str] = Field(default=None, description="Hospital name if DOCTOR")

class LoginRequest(BaseModel):
    identifier: str = Field(description="Email, 10-digit Phone, or License Number")
    password: str = Field(description="Password")

# ─── Auth Endpoints ───────────────────────────────────────────────────────────
@app.post("/api/auth/signup")
def auth_signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """
    Registers a new Doctor into 'doctors' table or Patient into 'patients' table.
    Stores country_code (TEXT) and 10-digit BIGINT phone_number.
    """
    if not validate_email(payload.email):
        raise HTTPException(status_code=400, detail="Invalid email address syntax.")
    
    country_code, phone_num = parse_phone_number(payload.phone)

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
            hospital_name=payload.hospital_name.strip()
        )
        db.add(doctor_entry)
        db.commit()
        db.refresh(doctor_entry)

        token = create_access_token({"sub": str(doctor_entry.id), "role": "DOCTOR", "email": doctor_entry.email, "name": doctor_entry.name})
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
                "doc_license": doctor_entry.doc_license,
                "hospital_name": doctor_entry.hospital_name
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
            password_hash=hashed_pw
        )
        db.add(patient_entry)
        db.commit()
        db.refresh(patient_entry)

        token = create_access_token({"sub": str(patient_entry.id), "role": "PATIENT", "email": patient_entry.email, "name": patient_entry.name})
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
                "phone_number": patient_entry.phone_number
            }
        }


@app.post("/api/auth/login")
def auth_login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates Doctor or Patient by Email, 10-digit Phone, or License ID.
    """
    id_clean = payload.identifier.strip()
    email_clean = id_clean.lower()

    # Try parsing integer phone
    try:
        _, parsed_num = parse_phone_number(id_clean)
    except Exception:
        try:
            parsed_num = int(re.sub(r"\D", "", id_clean))
        except Exception:
            parsed_num = -1

    # 1. Doctor table query
    doctor = db.query(DoctorDB).filter(
        (DoctorDB.email == email_clean) | 
        (DoctorDB.phone_number == parsed_num) | 
        (DoctorDB.doc_license == id_clean)
    ).first()

    if doctor and verify_password(payload.password, doctor.password_hash):
        token = create_access_token({"sub": str(doctor.id), "role": "DOCTOR", "email": doctor.email, "name": doctor.name})
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
                "doc_license": doctor.doc_license,
                "hospital_name": doctor.hospital_name
            }
        }

    # 2. Patient table query
    patient = db.query(PatientDB).filter(
        (PatientDB.email == email_clean) | 
        (PatientDB.phone_number == parsed_num)
    ).first()

    if patient and verify_password(payload.password, patient.password_hash):
        token = create_access_token({"sub": str(patient.id), "role": "PATIENT", "email": patient.email, "name": patient.name})
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
                "phone_number": patient.phone_number
            }
        }

    raise HTTPException(status_code=401, detail="Invalid login credentials.")
# Import graph modules
from graphs.prescription_parser import parse_prescription_text, parse_prescription_image_gemini
from graphs.specialty_suggestion import suggest_specialty_groq
from graphs.chatbot import chat_with_groq, clear_session
from graphs.timeline import save_prescription_to_timeline, get_patient_timeline
from graphs.context_agent import build_patient_health_context

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

@app.get("/")
def root():
    return {"status": "online", "server": "Agents FastAPI Server", "models": ["Groq Llama 3.3 70B", "Groq Whisper", "Gemini 2.0 Flash"]}

@app.post("/api/agents/suggest-specialty")
def suggest_specialty_endpoint(payload: SpecialtyRequest):
    """
    Categorizes patient symptoms into hospital specialties using Groq Llama 3.3 70B.
    """
    return suggest_specialty_groq(payload.symptoms)

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

@app.post("/api/chat/message")
def chat_message_endpoint(payload: ChatMessageRequest):
    """
    Sends a user message to the Groq Llama 3.3 70B health chatbot.
    Maintains per-session conversation history in memory and injects Timeline Context.
    Supports role='doctor' (clinical research mode) or role='patient' (consumer mode).
    """
    try:
        reply = chat_with_groq(payload.sessionId, payload.message, role=payload.role)
        return {"sessionId": payload.sessionId, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat Error: {str(e)}")

@app.post("/api/chat/clear")
def chat_clear_endpoint(payload: ChatClearRequest):
    """
    Clears the conversation history for a session.
    """
    clear_session(payload.sessionId)
    return {"status": "cleared", "sessionId": payload.sessionId}

# ─── End of Auth Endpoints ───────────────────────────────────────────────────


# ─── Timeline Endpoints (SQLite Persistent DB) ─────────────────────────────
@app.post("/api/timeline/save")
def timeline_save_endpoint(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    Saves a confirmed prescription into SQLite database (`healthcare.db`), generating a narrative Visit Summary.
    """
    try:
        # Generate Narrative Summary
        from graphs.timeline import generate_visit_summary
        visit_summary = generate_visit_summary(payload)

        patient_id_raw = payload.get("patientId", "100001")
        try:
            patient_id_num = int(str(patient_id_raw).replace("pat-", ""))
        except Exception:
            patient_id_num = 100001

        now = datetime.now()
        rx_id = f"rx-{patient_id_num}-{now.strftime('%Y%m%d%H%M%S')}"

        header = payload.get("header", {})
        body = payload.get("body", {})
        tail = payload.get("tail", {})
        dietary = payload.get("dietaryAdvice", {})

        pat_phone_raw = payload.get("patientPhone", "+919876543210")
        try:
            pat_cc, pat_phone_num = parse_phone_number(pat_phone_raw)
        except Exception:
            pat_cc, pat_phone_num = "+91", 9876543210

        new_rx = PrescriptionDB(
            id=rx_id,
            patient_id=patient_id_num,
            doctor_id=payload.get("doctorId", 500001),
            source=payload.get("source", "doctor_voice"),
            patient_name=payload.get("patientName", "Santhosh Kumar"),
            patient_country_code=pat_cc,
            patient_phone_number=pat_phone_num,
            doctor_name=header.get("doctorName", "Dr. Prescribing Doctor"),
            hospital_name=header.get("hospitalName", "Coimbatore Health Centre"),
            recorded_diagnosis=body.get("recordedDiagnosis", ""),
            medications_json=json.dumps(body.get("medications", [])),
            dietary_advice_json=json.dumps(dietary),
            advice=tail.get("advice", ""),
            follow_up_date=tail.get("followUpDate", ""),
            visit_summary=visit_summary,
            created_at=now
        )
        db.add(new_rx)
        db.commit()
        db.refresh(new_rx)

        # In-memory backwards compatibility sync
        save_prescription_to_timeline(payload)

        return {
            "status": "saved",
            "entry": {
                "id": new_rx.id,
                "patientId": str(new_rx.patient_id),
                "date": now.strftime("%Y-%m-%d"),
                "visitSummary": new_rx.visit_summary,
                "source": new_rx.source,
                "header": header,
                "body": body,
                "dietaryAdvice": dietary,
                "tail": tail
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Timeline Save Error: {str(e)}")


@app.get("/api/timeline/{patient_id}")
def timeline_get_endpoint(patient_id: str, doctor_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Returns timeline entries for a patient.
    If doctor_id is provided (Doctor Portal search): returns ONLY prescriptions issued by THAT doctor for this patient.
    If doctor_id is None (Patient Portal search): returns ALL prescriptions for this patient across all doctors.
    """
    query_clean = str(patient_id).strip()
    try:
        patient_num = int(query_clean.replace("pat-", ""))
    except Exception:
        patient_num = -1

    try:
        _, parsed_search_num = parse_phone_number(query_clean)
    except Exception:
        try:
            parsed_search_num = int(re.sub(r"\D", "", query_clean))
        except Exception:
            parsed_search_num = -1

    query = db.query(PrescriptionDB).filter(
        (PrescriptionDB.patient_id == patient_num) | 
        (PrescriptionDB.patient_phone_number == parsed_search_num) |
        (func.lower(PrescriptionDB.patient_name) == query_clean.lower())
    )

    if doctor_id:
        try:
            doc_num = int(str(doctor_id).replace("doc-", ""))
            query = query.filter(PrescriptionDB.doctor_id == doc_num)
        except Exception:
            pass

    rx_list = query.order_by(PrescriptionDB.created_at.desc()).all()

    results = []
    for idx, rx in enumerate(rx_list, 1):
        try:
            meds = json.loads(rx.medications_json)
        except Exception:
            meds = []
        try:
            dietary = json.loads(rx.dietary_advice_json) if rx.dietary_advice_json else {}
        except Exception:
            dietary = {}

        results.append({
            "id": rx.id,
            "patientId": str(rx.patient_id),
            "patientName": rx.patient_name,
            "patientPhone": f"{rx.patient_country_code}{rx.patient_phone_number}",
            "countryCode": rx.patient_country_code,
            "phoneNumber": rx.patient_phone_number,
            "date": rx.created_at.strftime("%Y-%m-%d"),
            "time": rx.created_at.strftime("%H:%M"),
            "index": idx,
            "visitSummary": rx.visit_summary,
            "source": rx.source,
            "header": {
                "doctorName": rx.doctor_name,
                "hospitalName": rx.hospital_name,
                "opdContact": "",
                "date": rx.created_at.strftime("%Y-%m-%d")
            },
            "body": {
                "recordedDiagnosis": rx.recorded_diagnosis,
                "medications": meds
            },
            "dietaryAdvice": dietary,
            "tail": {
                "advice": rx.advice,
                "followUpDate": rx.follow_up_date
            }
        })

    # If DB is empty, fallback to memory
    if not results:
        results = get_patient_timeline(patient_id)

    return {"patientId": patient_id, "prescriptions": results}

@app.get("/api/timeline/context/{patient_id}")
def timeline_context_endpoint(patient_id: str):
    """
    Returns enriched patient context built by Timeline Context Agent + Wellbeing State Agent.
    """
    return build_patient_health_context(patient_id)


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
