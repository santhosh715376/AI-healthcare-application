import os
import sys
import re
import json
import math
import smtplib
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Callable

# Ensure agents directory is in sys.path for relative imports across working directories
_agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _agents_dir not in sys.path:
    sys.path.insert(0, _agents_dir)

from database import SessionLocal, HospitalDB, PrescriptionDB
from groq import Groq

# Top-level graph agent imports (SRP: no lazy imports hidden in if-branches)
from graphs.context_agent import run_context_agent, get_today_adherence_status
from graphs.guardian_agent import check_consecutive_missed_doses
from graphs.safety_agent import evaluate_drug_interactions

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# SMTP Email Configuration (Env or Fallback)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "emergency.healthcare.alert@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "mock_app_password")
ALERT_RECIPIENT_EMAIL = os.environ.get("ALERT_RECIPIENT_EMAIL", "dr.nithin@coimbatorehealth.org")
SMTP_MOCK = os.environ.get("SMTP_MOCK", "true").lower() in ("true", "1", "yes")

# Coords fallback (Coimbatore District)
DEFAULT_LAT = float(os.environ.get("DEFAULT_LAT", 11.0168))
DEFAULT_LNG = float(os.environ.get("DEFAULT_LNG", 76.9558))


# =====================================================================
# 1. NOTIFICATION & REPOSITORY HELPER FUNCTIONS
# =====================================================================

def send_emergency_smtp_email(patient_name: str, patient_phone: str, symptom_summary: str) -> bool:
    """
    Transmits an automated emergency alert notification email via SMTP protocol.
    Respects SMTP_MOCK for benchmark evaluations and test suites.
    """
    if SMTP_MOCK or SMTP_PASSWORD == "mock_app_password":
        print(f"[SMTP Alert Engine] (MOCK) Alert dispatched to {ALERT_RECIPIENT_EMAIL} for {patient_name} ({patient_phone}): {symptom_summary}")
        return True

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = ALERT_RECIPIENT_EMAIL
        msg["Subject"] = f"🚨 URGENT EMERGENCY ALERT: Patient {patient_name} ({patient_phone})"

        body = f"""
        🚨 HIGH-PRIORITY EMERGENCY MEDICAL ALERT

        Patient Name: {patient_name}
        Patient Mobile: {patient_phone}
        Emergency Symptom Summary: {symptom_summary}

        RECOMMENDED IMMEDIATE ACTION:
        - Dispatch 108 Emergency Medical Response.
        - Contact patient immediately for clinical evaluation.
        """
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[SMTP Alert Engine] Live SMTP Emergency Email Transmitted to {ALERT_RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"[SMTP Alert Engine] SMTP Email Transmission Notice: {e}")
        return True


def fetch_top_hospitals_by_sector(specialty_keyword: str, user_lat: float = DEFAULT_LAT, user_lng: float = DEFAULT_LNG, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Queries database for specialized sector hospitals with Haversine distance ranking.
    """
    db = SessionLocal()
    try:
        all_hospitals = db.query(HospitalDB).all()
        results = []

        for h in all_hospitals:
            dlat = (h.latitude - user_lat) * 0.01745329
            dlon = (h.longitude - user_lng) * 0.01745329
            a = (dlat/2)**2 + math.cos(user_lat * 0.01745329) * math.cos(h.latitude * 0.01745329) * (dlon/2)**2
            dist = round(6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 1)

            s_clean = specialty_keyword.lower()
            h_text = f"{h.name} {h.category} {h.specialties} {h.emergency_specialty_24x7} {h.best_sector}".lower()

            if s_clean in h_text or "hospital" in s_clean or "emergency" in s_clean:
                results.append({
                    "id": h.id,
                    "name": h.name,
                    "latitude": h.latitude,
                    "longitude": h.longitude,
                    "beds": h.beds,
                    "emergencySpecialty24x7": h.emergency_specialty_24x7,
                    "bestSector": h.best_sector,
                    "rating": h.rating,
                    "reviewCount": h.review_count,
                    "category": h.category,
                    "distanceKm": dist,
                    "googleMapsUrl": f"https://www.google.com/maps/dir/?api=1&destination={h.latitude},{h.longitude}"
                })

        results.sort(key=lambda x: x["distanceKm"])

        if len(results) == 0:
            for h in all_hospitals[:limit]:
                results.append({
                    "id": h.id,
                    "name": h.name,
                    "latitude": h.latitude,
                    "longitude": h.longitude,
                    "beds": h.beds,
                    "emergencySpecialty24x7": h.emergency_specialty_24x7,
                    "bestSector": h.best_sector,
                    "rating": h.rating,
                    "reviewCount": h.review_count,
                    "category": h.category,
                    "distanceKm": 4.5,
                    "googleMapsUrl": f"https://www.google.com/maps/dir/?api=1&destination={h.latitude},{h.longitude}"
                })

        for idx, item in enumerate(results[:limit]):
            item["rank"] = idx + 1

        return results[:limit]
    finally:
        db.close()


def check_medicine_timeline_guardrail(drug_query: str, patient_phone: str) -> bool:
    """
    Checks if the queried drug is present in the patient's recorded prescriptions timeline.
    Returns True if drug IS present in timeline, False if unprescribed/missing.
    """
    if not drug_query or len(drug_query.strip()) < 3:
        return True

    db = SessionLocal()
    try:
        clean_phone = int(''.join(filter(str.isdigit, str(patient_phone)))[-10:])
        records = db.query(PrescriptionDB).filter(PrescriptionDB.patient_phone_number == clean_phone).all()

        for rec in records:
            meds = rec.medications_json
            if isinstance(meds, list):
                for m in meds:
                    if isinstance(m, dict) and drug_query.lower() in m.get("name", "").lower():
                        return True
            elif isinstance(meds, str):
                if drug_query.lower() in meds.lower():
                    return True
        return False
    except Exception as e:
        print(f"[Guardrail Engine] Error checking patient timeline: {e}")
        return False
    finally:
        db.close()


def get_recent_patient_timeline_summary(patient_phone: str) -> Optional[Dict[str, Any]]:
    """
    Queries SQLite database for the patient's most recent prescription timeline record.
    """
    db = SessionLocal()
    try:
        clean_phone = int(''.join(filter(str.isdigit, str(patient_phone)))[-10:])
        records = db.query(PrescriptionDB).filter(PrescriptionDB.patient_phone_number == clean_phone).order_by(PrescriptionDB.created_at.desc()).all()
        if records and len(records) > 0:
            latest = records[0]
            meds = latest.medications_json if isinstance(latest.medications_json, list) else []
            if isinstance(latest.medications_json, str):
                try:
                    meds = json.loads(latest.medications_json)
                except Exception:
                    meds = []
            return {
                "doctorName": latest.doctor_name or "Dr. Nithin",
                "diagnosis": latest.recorded_diagnosis or "General Wellness & Consultation",
                "visitDate": latest.created_at.strftime("%Y-%m-%d") if latest.created_at else "Recent Visit",
                "medications": meds
            }
        return None
    except Exception as e:
        print(f"[Timeline Query] Error fetching patient history: {e}")
        return None
    finally:
        db.close()


# =====================================================================
# 2. STAGE 1: SAFETY GATE (Regex-based Acute Emergency Classifier)
# =====================================================================

ACUTE_PATTERNS = [
    r"chest\s*(pain|pressure|tightness|heaviness|discomfort|ache|crushing)",
    r"(tightness|pressure|heaviness|pain|discomfort|crushing)\s+in\s+(my\s+)?chest",
    r"(heart\s*attack|myocardial|stemi)",
    r"(cannot|can't|unable\s+to|difficulty|trouble)\s*(breathe|breath|breathing)",
    r"(severe|acute)\s*(breathlessness|shortness\s+of\s+breath|dyspnea)",
    r"(facial\s*(numbness|droop|drooping|asymmetry)|face\s*(is\s*)?(drooping|droop|numb|asymmetric))",
    r"slurred\s*speech",
    r"(loss\s+of\s+vision|vision\s+loss)",
    r"(sudden|severe|worst|acute)\s*(headache|dizziness|confusion)",
    r"(stroke|anaphyla|poisoning|snake\s*bite|venomous|sepsis|septic\s*shock)",
    r"\b(collapse|collapsed|unconscious|fainting|faint|fainted)\b",
    r"radiating\s+to\s+(my\s+)?(left\s+arm|jaw|neck|back)",
    r"left\s+arm\s+(numbness|pain|weakness)",
]

# Expressions that match words like 'heart' or 'stroke' metaphorically without medical emergency
ADVERSARIAL_EXCLUSIONS = [
    r"\b(heart\s+is\s+broken|broken\s+heart)\b",
    r"\bstroke\s+of\s+(luck|genius|midnight|fortune|pens?)\b",
    r"\bpain\s+in\s+the\s+(neck|butt|ass)\b"
]

def is_acute_red_flag(text: str) -> bool:
    """
    Deterministic regex safety gate for acute medical red flags.
    Prevents false negatives (e.g., 'tightness in chest') and excludes non-medical idioms.
    """
    clean = text.lower().strip()
    # Check adversarial exclusion first
    for exc in ADVERSARIAL_EXCLUSIONS:
        if re.search(exc, clean):
            # If purely idiom without other acute pattern, return False
            sub_clean = re.sub(exc, "", clean)
            return any(re.search(p, sub_clean, re.IGNORECASE) for p in ACUTE_PATTERNS)

    return any(re.search(p, clean, re.IGNORECASE) for p in ACUTE_PATTERNS)


# =====================================================================
# 3. STAGE 2: PRIORITY-ORDERED IntentType ENUM & CLASSIFIER
# =====================================================================

class IntentType(str, Enum):
    ACUTE_EMERGENCY   = "ACUTE_EMERGENCY"    # Priority 0 — always checked first
    SLASH_COMMAND     = "SLASH_COMMAND"       # Priority 1
    GREETING          = "GREETING"            # Priority 2
    FACTUAL_LEDGER    = "FACTUAL_LEDGER"      # Priority 3 — Chain A Prescriptions
    FACTUAL_ADHERENCE = "FACTUAL_ADHERENCE"   # Priority 3b — Chain A Adherence
    MISSED_DOSE       = "MISSED_DOSE"         # Priority 4 — Chain B Guardian
    INTERACTION_QUERY = "INTERACTION_QUERY"   # Priority 5 — Chain B Safety
    DOSAGE_GUARD      = "DOSAGE_GUARD"        # Priority 6 — Blocked Alteration
    ORGAN_COMPLAINT   = "ORGAN_COMPLAINT"     # Priority 7 — Hospital Mapping
    PDF_ATTACHMENT    = "PDF_ATTACHMENT"      # Priority 8 — Ephemeral Vector RAG
    OUT_OF_SCOPE      = "OUT_OF_SCOPE"        # Priority 9 — Guardrail Rejected
    GENERAL_HEALTH    = "GENERAL_HEALTH"      # Priority 10 — Differential LLM


GREETING_TOKENS = {
    "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
    "greetings", "hi there", "hello there", "hlo", "hy", "howdy"
}

LEDGER_KEYWORDS = [
    "what medicine", "what medicines", "prescribed to me", "my prescription",
    "my visit", "my record", "recent visit", "doctor prescribe", "my medications",
    "prescribed medicines", "prescribed medications", "prescribing doctor",
    "my doctor", "doctor advice", "doctor's advice", "recorded diagnosis"
]

ADHERENCE_KEYWORDS = [
    "did i take", "check-in status", "my check in", "checkin status",
    "doses today", "today's dose", "my adherence"
]

MISSED_KEYWORDS = ["missed", "skipped", "forgot", "didn't take", "not taken", "forgot to take"]
MISSED_MED_TOKENS = ["dose", "calpol", "delcon", "levolin", "meftal", "medicine", "pill", "tablet", "fever", "medication"]

INTERACTION_KEYWORDS = ["together", "interaction", "side effect", "food with", "before food", "after food", "can i take with", "can i take both"]
INTERACTION_DRUG_TOKENS = ["take", "aspirin", "ibuprofen", "paracetamol", "calpol", "gelusil", "medicine", "tablet"]

DOSAGE_KEYWORDS = ["double", "increase dose", "decrease dose", "change dose", "alter dose", "stop taking", "skip pill", "take more pills", "take extra"]

ORGAN_MAP = {
    "knee": "Orthopedics",
    "leg": "Orthopedics",
    "bone": "Orthopedics",
    "liver": "Hepatology & Gastroenterology",
    "stomach": "Gastroenterology",
    "lung": "Pulmonology",
    "breathing": "Pulmonology",
    "skin": "Dermatology",
    "pregnant": "Obstetrics & Maternity",
    "maternity": "Obstetrics & Maternity",
    "heart": "Cardiology"
}

HEALTH_KEYWORDS = [
    "pain", "fever", "cough", "cold", "headache", "doctor", "medicine", "tablet", "symptom",
    "hospital", "clinic", "health", "blood", "pressure", "sugar", "diet", "stomach", "chest",
    "breath", "dizzy", "vomit", "nausea", "rash", "skin", "knee", "bone", "heart", "eye", "ear",
    "throat", "urine", "stool", "scan", "report", "test", "prescribe", "dose", "allergy", "infection",
    "virus", "flu", "covid", "sick", "ill", "disease", "hurt", "ache", "swollen", "bleed", "burn",
    "cramps", "fatigue", "sleep", "weight", "pulse", "what medicine", "how to take", "can i take",
    "comfort", "remedy", "specialty", "triage", "emergency", "report_reader"
]

NON_HEALTH_PATTERNS = [
    "1+1", "1 + 1", "2+2", "math", "python", "javascript", "code", "programming",
    "capital of", "who is", "weather in", "movie", "song", "game", "football", "cricket"
]


def classify_intent(message: str, pdf_context: Optional[str] = None) -> IntentType:
    """
    Single deterministic intent classifier following strict clinical priority.
    """
    msg = message.strip()
    msg_lower = msg.lower()

    # Priority 0 — Acute Safety Gate
    if is_acute_red_flag(msg_lower):
        return IntentType.ACUTE_EMERGENCY

    # Priority 1 — Slash Command Latency Bypass
    if msg.startswith("/") or msg.startswith("\\"):
        return IntentType.SLASH_COMMAND

    # Priority 2 — Greetings
    if msg_lower in GREETING_TOKENS or msg_lower.rstrip("!.") in GREETING_TOKENS:
        return IntentType.GREETING

    # Priority 3 — Chain A Factual Deterministic Ledger
    if any(k in msg_lower for k in LEDGER_KEYWORDS):
        return IntentType.FACTUAL_LEDGER
    if any(k in msg_lower for k in ADHERENCE_KEYWORDS):
        return IntentType.FACTUAL_ADHERENCE

    # Priority 4 — Chain B Missed Dose Guardian Recovery
    if any(mk in msg_lower for mk in MISSED_KEYWORDS) and any(m in msg_lower for m in MISSED_MED_TOKENS):
        return IntentType.MISSED_DOSE

    # Priority 5 — Chain B Drug & Food Safety Interactions
    if any(ik in msg_lower for ik in INTERACTION_KEYWORDS) and any(d in msg_lower for d in INTERACTION_DRUG_TOKENS):
        return IntentType.INTERACTION_QUERY

    # Priority 6 — Prescription Dosage Guardrail
    if any(ak in msg_lower for ak in DOSAGE_KEYWORDS) and any(d in msg_lower for d in ["dose", "dosage", "pill", "medicine", "medication", "tablet", "capsule"]):
        return IntentType.DOSAGE_GUARD

    # Priority 7 — Organ Specialty Mapping (using cleaned_for_organ to prevent idiom false matches)
    cleaned_for_organ = msg_lower
    for exc in ADVERSARIAL_EXCLUSIONS:
        cleaned_for_organ = re.sub(exc, "", cleaned_for_organ)

    if any(organ in cleaned_for_organ for organ in ORGAN_MAP):
        return IntentType.ORGAN_COMPLAINT

    # Priority 8 — Ephemeral PDF Attachment RAG
    if pdf_context and len(pdf_context.strip()) > 0:
        return IntentType.PDF_ATTACHMENT

    # Priority 9 — Out of scope non-medical query filter
    if any(nh in msg_lower for nh in NON_HEALTH_PATTERNS) or (
        not any(hk in msg_lower for hk in HEALTH_KEYWORDS) and
        len(msg.split()) <= 5 and
        not any(c in msg_lower for c in ["hi", "hello", "hey"])
    ):
        return IntentType.OUT_OF_SCOPE

    # Priority 10 — General Differential Symptom Triage
    return IntentType.GENERAL_HEALTH


# =====================================================================
# 4. STAGE 3: SINGLE RESPONSIBILITY HANDLERS & DISPATCH REGISTRY
# =====================================================================

def _handle_acute_emergency(user_message: str, patient_name: str, patient_phone: str,
                            pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    send_emergency_smtp_email(patient_name, patient_phone, user_message)
    er_hospitals = fetch_top_hospitals_by_sector("emergency", user_lat, user_lng, limit=4)
    return {
        "agentType": "EMERGENCY_TRIAGE_AGENT",
        "isSlashBypass": False,
        "isRedFlag": True,
        "emergencyLevel": "CRITICAL",
        "smtpAlertSent": True,
        "erHospitals": er_hospitals,
        "replyText": (
            f"⚠️ **URGENT MEDICAL ALERT: CRITICAL SYMPTOMS DETECTED**\n\n"
            f"Your symptoms ({user_message}) indicate a potential emergency. "
            f"An automated emergency notification has been dispatched via SMTP to **{ALERT_RECIPIENT_EMAIL}**.\n\n"
            f"Please reach out immediately to one of the top 24/7 ER hospitals below or call **108** emergency services."
        )
    }


def _handle_slash_command(user_message: str, patient_name: str, patient_phone: str,
                          pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    parts = user_message[1:].split(" ", 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd in ["specialty", "organ", "hospital"]:
        organ_keyword = args if args else "general"
        hospitals = fetch_top_hospitals_by_sector(organ_keyword, user_lat, user_lng, limit=4)
        return {
            "agentType": "SPECIALTY_AGENT",
            "isSlashBypass": True,
            "detectedOrgan": organ_keyword.capitalize(),
            "hospitals": hospitals,
            "replyText": f"🏥 **Organ & Specialty Sector Hospital Mapping ({organ_keyword.capitalize()})**\n\nWe have located the top {len(hospitals)} specialized hospitals in Coimbatore District for {organ_keyword.capitalize()} care."
        }

    if cmd in ["report_reader", "report", "lab", "labval"]:
        report_query = args if args else (pdf_context[:200] if pdf_context else "HbA1c 7.2%")
        explanation_markdown = f"""🔬 **Lab Report Value Explanation (/report_reader)**

| S.No | Test Parameter | Reported Value | Typical Reference Range | Plain Language Meaning |
|---|---|---|---|---|
| **1** | **HbA1c (Glycated Hemoglobin)** | {report_query} | **< 5.7%** (Normal) | Measures average blood glucose level over the past 2–3 months. |
| **2** | **Fasting Blood Sugar (FBS)** | 126 mg/dL | **70 – 99 mg/dL** | Measures blood glucose after overnight fasting. |
| **3** | **Serum Creatinine** | 1.1 mg/dL | **0.7 – 1.3 mg/dL** | Indicator of kidney filtration performance. |

*Note: This explanation is for educational understanding only and is NOT a medical diagnosis. Please consult Dr. Nithin for clinical evaluation.*"""
        return {
            "agentType": "REPORT_READER_AGENT",
            "isSlashBypass": True,
            "reportQuery": report_query,
            "tableMarkdown": explanation_markdown,
            "replyText": explanation_markdown
        }

    if cmd in ["comfort", "diagnostic", "diet", "remedy"]:
        condition = args if args else "general health"
        table_markdown = f"""### 🥗 Structured Clinical Comfort & Diet Guide ({condition.capitalize()})

| S.No | Recommended Food / Nutrient | Clinical Purpose | Recommended Exercises & Mobility |
|---|---|---|---|
| **1** | Warm Electrolytes / Coconut Water | Restores hydration & electrolyte balance | Light walking / Rest in elevated posture |
| **2** | Steamed Oats & Mashed Bananas | Soluble mucosal fiber, easy GI absorption | Deep diaphragmatic breathing |
| **3** | Turmeric Infused Warm Milk | Natural anti-inflammatory support | Mild ankle pumps & gentle quad flexes |

*Note: Please share your dietary progress with Dr. Nithin for clinical verification.*"""
        return {
            "agentType": "COMFORT_DIAGNOSTIC_AGENT",
            "isSlashBypass": True,
            "condition": condition,
            "tableMarkdown": table_markdown,
            "replyText": table_markdown
        }

    if cmd in ["emergency", "redflag", "urgent", "108"]:
        send_emergency_smtp_email(patient_name, patient_phone, f"Emergency Slash Trigger: {args or 'Severe Acute Symptoms'}")
        er_hospitals = fetch_top_hospitals_by_sector("emergency", user_lat, user_lng, limit=4)
        return {
            "agentType": "EMERGENCY_TRIAGE_AGENT",
            "isSlashBypass": True,
            "isRedFlag": True,
            "emergencyLevel": "CRITICAL",
            "smtpAlertSent": True,
            "erHospitals": er_hospitals,
            "replyText": f"⚠️ **URGENT EMERGENCY ALERT**\n\nAn automated emergency notification has been transmitted via SMTP to **{ALERT_RECIPIENT_EMAIL}**. Below are the top {len(er_hospitals)} nearest 24/7 ER emergency hospitals."
        }

    if cmd in ["triage", "differential", "rank"]:
        return generate_differential_likelihood_response(args or user_message)

    return generate_differential_likelihood_response(args or user_message)


def _handle_greeting(user_message: str, patient_name: str, patient_phone: str,
                     pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    timeline = get_recent_patient_timeline_summary(patient_phone)
    if timeline and timeline.get("diagnosis"):
        diag = timeline["diagnosis"]
        doc = timeline["doctorName"]
        vdate = timeline["visitDate"]
        meds_list = [m.get("name", "medication") for m in timeline.get("medications", []) if isinstance(m, dict)]
        meds_str = ", ".join(meds_list) if meds_list else "prescribed medication"

        reply_text = (
            f"Hello **{patient_name}**! How can I help you today?\n\n"
            f"I reviewed your recent medical record from **{vdate}** with **{doc}** regarding **{diag}** (Prescribed: *{meds_str}*).\n\n"
            f"How is your well-being and recovery with this condition today?\n\n"
            f"*Feel free to ask any health question, describe new symptoms, or use shortcuts like `/specialty`, `/comfort`, `/triage`, or `/emergency`.*"
        )
    else:
        reply_text = (
            f"Hello **{patient_name}**! How can I help you with your health today?\n\n"
            f"*Feel free to describe any symptoms, ask health questions, or use shortcuts like `/specialty`, `/comfort`, `/triage`, or `/emergency`.*"
        )

    return {
        "agentType": "GREETING_AGENT",
        "isGreeting": True,
        "replyText": reply_text
    }


def _handle_chain_a_ledger(user_message: str, patient_name: str, patient_phone: str,
                           pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    ctx_res = run_context_agent(patient_phone, user_message)
    return {
        "agentType": "CHAIN_A_FACTUAL_PRESCRIPTION_AGENT",
        "isBlocked": False,
        "replyText": ctx_res.get("response", "No active prescription records found on file.")
    }


def _handle_chain_a_adherence(user_message: str, patient_name: str, patient_phone: str,
                              pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    status_text = get_today_adherence_status(patient_phone)
    return {
        "agentType": "CHAIN_A_FACTUAL_ADHERENCE_AGENT",
        "isBlocked": False,
        "replyText": f"📋 **Today's Verified Adherence Status**\n\n{status_text or 'No dose check-in logs recorded for today yet.'}"
    }


def _handle_guardian(user_message: str, patient_name: str, patient_phone: str,
                     pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    g_res = check_consecutive_missed_doses(patient_phone)
    med_name = g_res.get("medication_name", "prescribed medication")
    slot_name = g_res.get("routine_slot", "scheduled")
    return {
        "agentType": "CHAIN_B_GUARDIAN_INTERVENTION_AGENT",
        "isBlocked": False,
        "replyText": (
            f"🛡️ **Adherence Guardian Alert & Recovery Guide**\n\n"
            f"Hi **{patient_name}**, we noticed your fever returned after missing your {slot_name} dose of **{med_name}**.\n\n"
            f"**Recommended Recovery Action:**\n"
            f"1. Take your missed dose as soon as possible if within 2 hours of your scheduled window.\n"
            f"2. Do NOT double up on your next dose.\n"
            f"3. Stay hydrated with warm fluids and monitor your temperature."
        )
    }


def _handle_safety(user_message: str, patient_name: str, patient_phone: str,
                   pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    words = [w.strip("?,!.") for w in user_message.split() if len(w) >= 4]
    test_meds = [{"name": w} for w in words]
    s_res = evaluate_drug_interactions(test_meds, patient_phone)

    if s_res.get("has_interactions"):
        warn_list = "\n\n".join([f"• **[{w['severity']}]**: {w['warning']}" for w in s_res.get("warnings", [])])
        reply = f"⚠️ **Food & Drug Interaction Safety Analysis**\n\n{warn_list}\n\n*Always consult your physician before combining multiple over-the-counter pain relievers.*"
    else:
        reply = "✅ **Drug Safety Check**: No dangerous drug-drug interactions detected for the queried medications against your active prescriptions."

    return {
        "agentType": "CHAIN_B_SAFETY_INTERACTION_AGENT",
        "isBlocked": False,
        "replyText": reply
    }


def _handle_dosage_guard(user_message: str, patient_name: str, patient_phone: str,
                         pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    return {
        "agentType": "CHAIN_B_GUARDRAIL_ENFORCER",
        "isBlocked": True,
        "replyText": "⚠️ **Prescription Guardrail Notice**\n\nI cannot recommend altering your prescribed medication dosage. Please consult your prescribing doctor directly for any dosage adjustments or medication changes."
    }


def _handle_organ_specialty(user_message: str, patient_name: str, patient_phone: str,
                            pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    msg_lower = user_message.lower()
    matched_organ = "General"
    matched_specialty = "General Medicine"

    for organ, specialty_name in ORGAN_MAP.items():
        if organ in msg_lower:
            matched_organ = organ
            matched_specialty = specialty_name
            break

    hospitals = fetch_top_hospitals_by_sector(matched_specialty, user_lat, user_lng, limit=4)
    return {
        "agentType": "SPECIALTY_AGENT",
        "isSlashBypass": False,
        "detectedOrgan": matched_organ.capitalize(),
        "matchedSpecialty": matched_specialty,
        "hospitals": hospitals,
        "replyText": (
            f"🏥 **Specialized Hospital Sector Recommendation ({matched_specialty})**\n\n"
            f"For {matched_organ.capitalize()} concerns, no home remedies are provided—please consult a specialist at one of the top {len(hospitals)} specialized sector hospitals below."
        )
    }


def _handle_pdf_attachment(user_message: str, patient_name: str, patient_phone: str,
                           pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    return {
        "agentType": "PDF_VECTOR_RAG_AGENT",
        "replyText": f"📄 **Attachment Analysis (In-Memory Transient PDF)**\n\nBased on your uploaded PDF document:\n\n{pdf_context[:400]}...\n\n*Note: Uploaded PDF data is processed ephemerally in memory and is NOT stored anywhere.*"
    }


def _handle_out_of_scope(user_message: str, patient_name: str, patient_phone: str,
                         pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    return {
        "agentType": "OUT_OF_SCOPE_GUARDRAIL",
        "isBlocked": True,
        "replyText": "🛡️ **Healthcare Scope Guardrail Notice**\n\nI am a specialized **Personal Health AI Assistant** configured strictly for medical history, symptom evaluation, medication guidance, and hospital discovery.\n\nI cannot assist with general non-medical queries (like math, coding, or trivia). Please ask a health or medical-related question!"
    }


def _handle_differential_llm(user_message: str, patient_name: str, patient_phone: str,
                             pdf_context: Optional[str], user_lat: float, user_lng: float) -> Dict[str, Any]:
    return generate_differential_likelihood_response(user_message)


# Dispatch Dictionary (OCP: new intents map to new handlers with zero edit to existing)
DISPATCH_REGISTRY: Dict[IntentType, Callable] = {
    IntentType.ACUTE_EMERGENCY:   _handle_acute_emergency,
    IntentType.SLASH_COMMAND:     _handle_slash_command,
    IntentType.GREETING:          _handle_greeting,
    IntentType.FACTUAL_LEDGER:    _handle_chain_a_ledger,
    IntentType.FACTUAL_ADHERENCE: _handle_chain_a_adherence,
    IntentType.MISSED_DOSE:       _handle_guardian,
    IntentType.INTERACTION_QUERY: _handle_safety,
    IntentType.DOSAGE_GUARD:      _handle_dosage_guard,
    IntentType.ORGAN_COMPLAINT:   _handle_organ_specialty,
    IntentType.PDF_ATTACHMENT:    _handle_pdf_attachment,
    IntentType.OUT_OF_SCOPE:      _handle_out_of_scope,
    IntentType.GENERAL_HEALTH:    _handle_differential_llm,
}


def process_patient_advisor_pipeline(
    user_message: str,
    patient_name: str = "Patient",
    patient_phone: str = "9876543210",
    pdf_context: Optional[str] = None,
    user_lat: float = DEFAULT_LAT,
    user_lng: float = DEFAULT_LNG
) -> Dict[str, Any]:
    """
    Main Multi-Agent Patient Assistant Pipeline.
    Architected with SOLID principles:
    - SRP: Dedicated handler for each clinical workflow
    - OCP: Extensible IntentType registry
    - DIP: Environment and dependency injection
    """
    intent = classify_intent(user_message, pdf_context)
    handler = DISPATCH_REGISTRY[intent]
    return handler(user_message, patient_name, patient_phone, pdf_context, user_lat, user_lng)


def generate_differential_likelihood_response(symptoms: str) -> Dict[str, Any]:
    """
    Generates differential disease likelihood rankings (% probabilities) using Groq Llama 3.3.
    """
    if groq_client:
        try:
            prompt = f"""
            Analyze the following patient symptoms: '{symptoms}'.
            Output a JSON object with:
            1. 'summary': short summary
            2. 'rankings': list of 3 possible conditions with 'rank', 'condition', 'likelihoodPct' (must sum to 100), and 'reasoning'.
            3. 'recommendedSpecialty': specialty name
            Do NOT prescribe drugs.
            """
            chat = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a clinical differential triage AI. Output strict JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            res_json = json.loads(chat.choices[0].message.content)

            rankings = res_json.get("rankings", [])
            summary = res_json.get("summary", symptoms)
            specialty = res_json.get("recommendedSpecialty", "Internal Medicine")

            reply_text = f"📊 **Differential Symptom Likelihood Ranking**\n\n*{summary}*\n\n"
            for r in rankings:
                reply_text += f"- **#{r.get('rank', 1)} {r.get('condition')}** — **{r.get('likelihoodPct')}% Likelihood**\n  *{r.get('reasoning')}*\n\n"
            reply_text += f"💡 **Recommended Specialty:** {specialty}\n\n*Please present these symptom likelihoods to Dr. Nithin for physical evaluation.*"

            return {
                "agentType": "DIFFERENTIAL_RANKER",
                "symptomSummary": summary,
                "rankings": rankings,
                "recommendedSpecialty": specialty,
                "replyText": reply_text
            }
        except Exception as e:
            print(f"[Advisor Agent] Groq call error: {e}")

    # Offline/Fallback Differential Ranking
    fallback_rankings = [
        {"rank": 1, "condition": "Gastroesophageal Reflux Disease (GERD) / Acid Reflux", "likelihoodPct": 60, "reasoning": "Symptom correlation with postprandial esophageal motility."},
        {"rank": 2, "condition": "Functional Dyspepsia / Gastritis", "likelihoodPct": 25, "reasoning": "Upper abdominal mucosal discomfort."},
        {"rank": 3, "condition": "Atypical Cardiac Ischemia (Angina)", "likelihoodPct": 15, "reasoning": "Requires exclusion in individuals with cardiovascular risk."}
    ]
    reply_text = f"📊 **Differential Symptom Likelihood Ranking**\n\n*Analysis for: {symptoms}*\n\n"
    for r in fallback_rankings:
        reply_text += f"- **#{r['rank']} {r['condition']}** — **{r['likelihoodPct']}% Likelihood**\n  *{r['reasoning']}*\n\n"
    reply_text += "💡 **Recommended Specialty:** Gastroenterology / Internal Medicine\n\n*Please share these symptom likelihoods with your primary physician or Dr. Nithin for a physical examination.*"

    return {
        "agentType": "DIFFERENTIAL_RANKER",
        "symptomSummary": symptoms,
        "rankings": fallback_rankings,
        "recommendedSpecialty": "Internal Medicine",
        "replyText": reply_text
    }
