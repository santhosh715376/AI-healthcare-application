"""
Context & Wellbeing Agents (agents/graphs/context_agent.py)
Agentic layer that reads timeline data and constructs enriched context blocks for the Chatbot.
"""

from typing import Dict, List, Any
from graphs.timeline import get_patient_timeline


def build_patient_health_context(patient_id: str = "pat-1001") -> Dict[str, Any]:
    """
    Timeline Context Agent & Wellbeing State Agent:
    Retrieves recent timeline entries and builds an enriched health context block
    for the Groq chatbot system prompt + frontend health status card.
    """
    timeline = get_patient_timeline(patient_id)

    if not timeline:
        return {
            "hasHistory": False,
            "statusCard": None,
            "systemPromptContext": "No recent patient prescription history on file."
        }

    latest = timeline[0]
    header = latest.get("header", {})
    body = latest.get("body", {})
    tail = latest.get("tail", {})

    doctor = header.get("doctorName", "Dr. Unspecified")
    hospital = header.get("hospitalName", "General Clinic")
    diagnosis = body.get("recordedDiagnosis", "Consultation")
    date_val = latest.get("date", "Recent")
    meds = body.get("medications", [])

    med_names = [m.get("name", "Medication") for m in meds]
    meds_str = ", ".join(med_names) if med_names else "Prescribed medications"

    # Frontend Health Status Card object
    status_card = {
        "visitedHospital": hospital,
        "date": date_val,
        "diagnosis": diagnosis,
        "doctor": doctor,
        "medicationsSummary": meds_str,
        "advice": tail.get("advice", "Follow doctor instructions."),
        "treatmentWindow": "Active Treatment Window"
    }

    # System Prompt Context Block for Groq Chatbot
    system_prompt_context = f"""
[PATIENT HEALTH CONTEXT — READ ONLY — DO NOT INVENT]
Most Recent Visit:
  Date: {date_val}
  Hospital: {hospital} ({header.get('opdContact', '')})
  Doctor: {doctor}
  Diagnosis: {diagnosis}
  Visit Summary: {latest.get('visitSummary', '')}
  Medications: {meds_str}
  Advice: {tail.get('advice', '')}

Rules for AI Chatbot:
- Use this context ONLY when patient asks about their visit, diagnosis, or prescribed medications.
- Never diagnose. Never modify prescription details.
"""

    return {
        "hasHistory": True,
        "statusCard": status_card,
        "systemPromptContext": system_prompt_context,
        "latestPrescription": latest
    }
