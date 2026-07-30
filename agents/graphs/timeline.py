"""
Prescription Timeline Manager (agents/graphs/timeline.py)
Handles storing, summarizing, and retrieving patient prescription history.
"""

import os
import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# In-Memory Timeline Store: { patientId: [ prescription_dict, ... ] }
TIMELINE_STORE: Dict[str, List[Dict[str, Any]]] = {}


def generate_visit_summary(prescription: Dict[str, Any]) -> str:
    """
    Generates a narrative Visit Summary sentence using Groq Llama 3.3 70B.
    Example: "Patient visited CHC Nemmara and was examined by Dr. Nithin Narayanan. Diagnosed with URTI."
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    header = prescription.get("header", {})
    body = prescription.get("body", {})

    doctor = header.get("doctorName", "the doctor")
    hospital = header.get("hospitalName", "the health center")
    diagnosis = body.get("recordedDiagnosis", "general consultation")
    date_str = header.get("date") or datetime.date.today().strftime("%Y-%m-%d")

    if groq_key and not groq_key.startswith("YOUR_"):
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            prompt = f"""
            Write a 1-sentence narrative visit summary for a medical timeline:
            Doctor: {doctor}
            Hospital: {hospital}
            Date: {date_str}
            Diagnosis: {diagnosis}

            Rules:
            - Exactly ONE clear narrative sentence.
            - Format: "Patient visited [Hospital] and was examined by [Doctor]. Diagnosed with [Diagnosis] on [Date]."
            - Do NOT include medication lists in this summary sentence.
            """
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=60,
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating summary via Groq: {e}")

    # Fallback summary sentence
    return f"Patient visited {hospital} and was examined by {doctor}. Diagnosed with {diagnosis} on {date_str}."


def save_prescription_to_timeline(prescription: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves a confirmed prescription into the patient's timeline record.
    Generates a visit summary and timestamps the entry.
    """
    patient_id = prescription.get("patientId", "pat-1001")

    if patient_id not in TIMELINE_STORE:
        TIMELINE_STORE[patient_id] = []

    existing = TIMELINE_STORE[patient_id]
    entry_index = len(existing) + 1

    now = datetime.datetime.now()
    entry = {
        "id": f"rx-tl-{patient_id[:4]}-{entry_index:03d}",
        "patientId": patient_id,
        "date": prescription.get("header", {}).get("date") or now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "index": entry_index,
        "visitSummary": generate_visit_summary(prescription),
        "source": prescription.get("source", "doctor_voice"),
        "header": prescription.get("header", {}),
        "body": prescription.get("body", {}),
        "tail": prescription.get("tail", {}),
        "timestamp": now.isoformat()
    }

    # Store newest-first
    TIMELINE_STORE[patient_id].insert(0, entry)
    print(f"[Timeline] Saved entry #{entry_index} for {patient_id}: {entry['visitSummary']}")
    return entry


def get_patient_timeline(patient_id: str = "pat-1001") -> List[Dict[str, Any]]:
    """
    Retrieves all timeline entries for a patient, sorted newest-first.
    """
    return TIMELINE_STORE.get(patient_id, [])
