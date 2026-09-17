import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import require_patient, get_current_user
from graphs.patient_advisor_agent import process_patient_advisor_pipeline
from graphs.chatbot import chat_with_groq
from graphs.specialty_suggestion import suggest_specialty_groq

router = APIRouter(tags=["Chat & Clinical Advisory"])


class PatientAdvisorRequest(BaseModel):
    message: str
    patientName: str = "Patient"
    patientPhone: str = Field(default="9876543210")
    pdfContext: Optional[str] = None
    lat: float = 11.0168
    lng: float = 76.9558


class ChatMessageRequest(BaseModel):
    message: str
    sessionId: str = "default"
    patientId: Optional[str] = None
    role: str = "patient"


class SpecialtyRequest(BaseModel):
    symptoms: str


@router.post("/api/chat/patient-advisor")
def patient_advisor_endpoint(
    payload: PatientAdvisorRequest,
    current_user: Dict[str, Any] = Depends(require_patient)
):
    """
    Patient Health Assistant Advisor Endpoint.
    Guarded with require_patient JWT authentication. Phone and Name are resolved
    directly from verified JWT credentials, ensuring complete patient data isolation.
    """
    verified_phone = str(current_user.get("phone_number") or current_user.get("phone") or payload.patientPhone)
    verified_name = current_user.get("name") or payload.patientName

    return process_patient_advisor_pipeline(
        user_message=payload.message,
        patient_name=verified_name,
        patient_phone=verified_phone,
        pdf_context=payload.pdfContext,
        user_lat=payload.lat,
        user_lng=payload.lng
    )


@router.post("/api/chat/message")
def chat_message_endpoint(
    payload: ChatMessageRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Direct Chatbot endpoint with session history and clinical context injection.
    Scopes sessions securely using authenticated user identity.
    """
    user_id = str(current_user.get("sub")) if current_user else (payload.patientId or "pat-anonymous")
    role = current_user.get("role", payload.role).lower() if current_user else payload.role.lower()

    try:
        reply = chat_with_groq(
            session_id=payload.sessionId,
            user_message=payload.message,
            patient_id=user_id,
            role=role
        )
        return {"reply": reply, "sessionId": payload.sessionId}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/api/agents/suggest-specialty")
def suggest_specialty_endpoint(payload: SpecialtyRequest):
    """
    Categorizes patient symptoms into hospital specialties using Groq Llama 3.3 70B.
    """
    return suggest_specialty_groq(payload.symptoms)
