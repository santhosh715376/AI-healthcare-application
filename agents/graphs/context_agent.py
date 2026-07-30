import os
import json
import requests
from typing import Dict, Any, Optional
from database import SessionLocal, PrescriptionDB, AdherenceScheduleDB, AdherenceLogDB, PatientDB
from datetime import datetime

GUARDRAIL_DISCLAIMER = "I cannot alter your prescribed medication dosage or recommend unprescribed treatments. Please consult your prescribing doctor directly for any medication changes."

def get_today_adherence_status(patient_phone: int) -> str:
    db = SessionLocal()
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        logs = db.query(AdherenceLogDB).filter(AdherenceLogDB.scheduled_date == today_str).all()
        if not logs:
            return ""
        taken = [f"{l.medication_name} ({l.routine_slot})" for l in logs if l.status == "TAKEN"]
        due = [f"{l.medication_name} ({l.routine_slot})" for l in logs if l.status == "DUE"]
        parts = []
        if taken:
            parts.append(f"Verified Taken Doses: {', '.join(taken)}")
        if due:
            parts.append(f"Pending Due Doses: {', '.join(due)}")
        return " | ".join(parts)
    except Exception as e:
        print(f"[ContextAgent] Adherence lookup error: {e}")
        return ""
    finally:
        db.close()

def get_latest_patient_prescription(patient_identifier: Any) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        import re
        raw_str = str(patient_identifier).strip()
        digits = re.sub(r"\D", "", raw_str)
        phone_10 = int(digits[-10:]) if len(digits) >= 10 else -1
        pat_id_num = int(digits) if len(digits) > 0 and len(digits) < 10 else -1

        # Find canonical patient record
        patient = db.query(PatientDB).filter(
            (PatientDB.id == pat_id_num) | 
            (PatientDB.phone_number == phone_10) |
            (PatientDB.id == phone_10)
        ).first()

        real_pat_id = patient.id if patient else (pat_id_num if pat_id_num != -1 else phone_10)
        real_phone = patient.phone_number if patient else phone_10

        rx = db.query(PrescriptionDB).filter(
            (PrescriptionDB.patient_id == real_pat_id) |
            (PrescriptionDB.patient_phone_number == real_phone) |
            (PrescriptionDB.patient_phone_number == phone_10) |
            (PrescriptionDB.patient_id == phone_10)
        ).order_by(PrescriptionDB.created_at.desc()).first()

        if not rx:
            return None
        return {
            "id": rx.id,
            "patient_name": rx.patient_name,
            "doctor_name": rx.doctor_name,
            "hospital_name": rx.hospital_name,
            "recorded_diagnosis": rx.recorded_diagnosis,
            "medications": json.loads(rx.medications_json) if rx.medications_json else [],
            "advice": rx.advice,
            "created_at": rx.created_at.strftime("%B %d, %Y") if rx.created_at else "Recent Visit"
        }
    except Exception as e:
        print(f"[ContextAgent] Error fetching prescription: {e}")
        return None
    finally:
        db.close()

def run_context_agent(patient_phone: int, user_query: str) -> Dict[str, Any]:
    rx_data = get_latest_patient_prescription(patient_phone)
    query_lower = user_query.lower().strip()

    # 1. Greeting Fast-Path
    if query_lower in ["hi", "hello", "hey", "good morning", "good evening", "greetings"]:
        if rx_data:
            med_names = ", ".join([m.get("name", "") for m in rx_data["medications"]])
            msg = f"Hello {rx_data['patient_name']}! How can I help you today?\n\nI reviewed your recent medical record from {rx_data['created_at']} with {rx_data['doctor_name']} regarding {rx_data['recorded_diagnosis']} (Prescribed: {med_names}).\n\nHow is your well-being and recovery with this condition today?"
        else:
            msg = "Hello! Welcome to Healthcare Continuity. How can I assist you with your health today?"
        return {"response": msg, "guardrail_triggered": False}

    # 2. Dosage Alteration Safety Guardrail
    dosage_keywords = ["double", "increase", "decrease", "change dose", "alter dose", "stop taking", "skip", "take more", "take extra"]
    if any(k in query_lower for k in dosage_keywords) and any(d in query_lower for d in ["dose", "dosage", "pill", "medicine", "medication", "tablet", "capsule"]):
        doctor_name = rx_data['doctor_name'] if rx_data else "your prescribing doctor"
        return {
            "response": f"I cannot alter your prescribed medication dosage. Please consult {doctor_name} directly for any medication changes.",
            "guardrail_triggered": True
        }

    # 3. Grounded LLM Contextual Synthesis
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or not rx_data:
        if rx_data:
            med_info = ", ".join([f"{m.get('name')} ({m.get('dosage', '')})" for m in rx_data['medications']])
            return {
                "response": f"According to your medical record from {rx_data['created_at']} with {rx_data['doctor_name']} for {rx_data['recorded_diagnosis']}, you were prescribed: {med_info}. Advice: {rx_data.get('advice', 'Take as directed')}.",
                "guardrail_triggered": False
            }
        return {"response": "I checked your medical profile, but no active prescriptions are recorded on file yet. Please scan your paper prescription using Gemini OCR to populate your record.", "guardrail_triggered": False}

    prompt = f"""You are a grounded clinical assistant. Answer the patient's question strictly using their official recorded medical history.

RECORDED HISTORY:
- Patient Name: {rx_data['patient_name']}
- Prescribing Doctor: {rx_data['doctor_name']} ({rx_data['hospital_name']})
- Visit Date: {rx_data['created_at']}
- Recorded Diagnosis: {rx_data['recorded_diagnosis']}
- Prescribed Medications JSON: {json.dumps(rx_data['medications'])}
- Doctor Advice: {rx_data['advice']}

PATIENT QUESTION:
"{user_query}"

INSTRUCTIONS:
- Explain clearly and compassionately how their prescribed medicines relate to their recorded diagnosis.
- Do NOT invent new medications, dosages, or unrecorded diagnoses.
- Keep response under 3 sentences.

RESPONSE:"""

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
        content = res.json()["choices"][0]["message"]["content"]
        return {"response": content.strip(), "guardrail_triggered": False}
    except Exception as e:
        print(f"[ContextAgent] Groq API error: {e}")
        return {"response": f"According to your record with {rx_data['doctor_name']} for {rx_data['recorded_diagnosis']}, your prescribed medicines are: {json.dumps(rx_data['medications'])}.", "guardrail_triggered": False}
