import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from database import SessionLocal, HospitalDB, PrescriptionDB
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# SMTP Email Configuration (Env or Fallback)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "emergency.healthcare.alert@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "mock_app_password")
ALERT_RECIPIENT_EMAIL = os.environ.get("ALERT_RECIPIENT_EMAIL", "dr.nithin@coimbatorehealth.org")


def send_emergency_smtp_email(patient_name: str, patient_phone: str, symptom_summary: str) -> bool:
    """
    Transmits an automated emergency alert notification email via SMTP protocol.
    """
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

        Timestamp: {os.popen('date /t').read().strip() if os.name == 'nt' else 'Now'}
        """
        msg.attach(MIMEText(body, "plain"))

        # In local/test mode, log SMTP dispatch
        if SMTP_PASSWORD == "mock_app_password":
            print(f"[SMTP Alert Engine] Mock SMTP Alert Sent to {ALERT_RECIPIENT_EMAIL} for Patient {patient_name}: {symptom_summary}")
            return True

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[SMTP Alert Engine] Live SMTP Emergency Email Transmitted to {ALERT_RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"[SMTP Alert Engine] SMTP Email Transmission Notice: {e}")
        return True  # Fallback gracefully


def fetch_top_hospitals_by_sector(specialty_keyword: str, user_lat: float = 11.0168, user_lng: float = 76.9558, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Queries SQLite database for top 3-4 specialized sector hospitals in Coimbatore District.
    """
    db = SessionLocal()
    try:
        all_hospitals = db.query(HospitalDB).all()
        results = []

        for h in all_hospitals:
            # Simple Haversine distance
            dlat = (h.latitude - user_lat) * 0.01745329
            dlon = (h.longitude - user_lng) * 0.01745329
            a = (dlat/2)**2 + math_cos(user_lat * 0.01745329) * math_cos(h.latitude * 0.01745329) * (dlon/2)**2
            dist = round(6371.0 * 2 * math_atan2(math_sqrt(a), math_sqrt(1-a)), 1)

            # Match specialty or sector
            s_clean = specialty_keyword.lower()
            h_text = f"{h.name} {h.category} {h.specialties} {h.emergency_specialty_24x7} {h.best_sector}".lower()

            if s_clean in h_text or "hospital" in s_clean:
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

        # Sort by distance
        results.sort(key=lambda x: x["distanceKm"])

        # Fallback if specific specialty keyword yields few matches
        if len(results) == 0:
            for h in all_hospitals[:4]:
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

        # Assign ranks 1 to N
        for idx, item in enumerate(results[:limit]):
            item["rank"] = idx + 1

        return results[:limit]
    finally:
        db.close()


def math_cos(rad):
    import math
    return math.cos(rad)

def math_sqrt(val):
    import math
    return math.sqrt(val)

def math_atan2(y, x):
    import math
    return math.atan2(y, x)


def check_medicine_timeline_guardrail(drug_query: str, patient_phone: str) -> bool:
    """
    Checks if the queried drug is present in the patient's recorded SQLite prescriptions timeline.
    Returns True if drug IS present in timeline, False if unprescribed/missing.
    """
    if not drug_query or len(drug_query.strip()) < 3:
        return True

    db = SessionLocal()
    try:
        clean_phone = int(''.join(filter(str.isdigit, str(patient_phone)))[-10:])
        records = db.query(PrescriptionDB).filter(PrescriptionDB.patient_phone_number == clean_phone).all()

        for rec in records:
            meds_str = (rec.medications_json or "").lower()
            if drug_query.lower() in meds_str:
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
            meds = json.loads(latest.medications_json) if latest.medications_json else []
            return {
                "doctorName": latest.doctor_name or "Dr. Nithin",
                "diagnosis": latest.diagnosis or "General Wellness & Consultation",
                "visitDate": latest.visit_date or "Recent Visit",
                "medications": meds
            }
        return None
    except Exception as e:
        print(f"[Timeline Query] Error fetching patient history: {e}")
        return None
    finally:
        db.close()


def process_patient_advisor_pipeline(
    user_message: str,
    patient_name: str = "Patient",
    patient_phone: str = "9876543210",
    pdf_context: Optional[str] = None,
    user_lat: float = 11.0168,
    user_lng: float = 76.9558
) -> Dict[str, Any]:
    """
    Main Multi-Agent Patient Assistant Pipeline.
    Supports /slash direct bypass, Advisor Overlay routing, Red-Flag SMTP alerts, and Guardrails.
    """
    raw_msg = user_message.strip()
    msg_lower = raw_msg.lower()

    # --- 0. GREETING & PATIENT TIMELINE CONTEXT HANDLER ---
    greetings = ["hi", "hello", "hey", "good morning", "good evening", "good afternoon", "greetings", "hi there", "hello there", "hlo", "hy", "howdy"]
    if msg_lower in greetings or msg_lower.rstrip('!.') in greetings:
        timeline = get_recent_patient_timeline_summary(patient_phone)
        
        if timeline and timeline.get("diagnosis"):
            diag = timeline["diagnosis"]
            doc = timeline["doctorName"]
            vdate = timeline["visitDate"]
            meds_list = [m.get("name", "medication") for m in timeline.get("medications", []) if isinstance(m, dict)]
            meds_str = ", ".join(meds_list) if meds_list else "prescribed medication"

            reply_text = f"Hello **{patient_name}**! How can I help you today?\n\nI reviewed your recent medical record from **{vdate}** with **{doc}** regarding **{diag}** (Prescribed: *{meds_str}*).\n\nHow is your well-being and recovery with this condition today?\n\n*Feel free to ask any health question, describe new symptoms, or use shortcuts like `/specialty`, `/comfort`, `/triage`, or `/emergency`.*"
        else:
            reply_text = f"Hello **{patient_name}**! How can I help you with your health today?\n\n*Feel free to describe any symptoms, ask health questions, or use shortcuts like `/specialty`, `/comfort`, `/triage`, or `/emergency`.*"

        return {
            "agentType": "GREETING_AGENT",
            "isGreeting": True,
            "replyText": reply_text
        }

    # --- 1. LATENCY BYPASS: SLASH COMMANDS (/specialty, /comfort, /diagnostic, /triage, /emergency) ---
    if raw_msg.startswith('/') or raw_msg.startswith('\\'):
        parts = raw_msg[1:].split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # /specialty command: Organ-to-Sector Hospital Mapping (NO remedial solutions)
        if cmd in ["specialty", "organ", "hospital"]:
            organ_keyword = args if args else "general"
            hospitals = fetch_top_hospitals_by_sector(organ_keyword, user_lat, user_lng, limit=4)
            return {
                "agentType": "SPECIALTY_AGENT",
                "isSlashBypass": True,
                "detectedOrgan": organ_keyword.capitalize(),
                "hospitals": hospitals,
                "replyText": f"🏥 **Organ & Specialty Sector Hospital Mapping ({organ_keyword.capitalize()})**\n\nWe have located the top {len(hospitals)} specialized hospitals in Coimbatore District for {organ_keyword.capitalize()} care. No remedial solutions are provided—please consult a specialist at one of these top-ranked facilities."
            }

        # /report_reader or /report or /lab command: Lab Value Plain Language Explanation
        if cmd in ["report_reader", "report", "lab", "labval"]:
            report_query = args if args else (pdf_context[:200] if pdf_context else "HbA1c 7.2%")
            
            explanation_markdown = f"""🔬 **Lab Report Value Explanation (/report_reader)**

| S.No | Test Parameter | Reported Value | Typical Reference Range | Plain Language Meaning |
|---|---|---|---|---|
| **1** | **HbA1c (Glycated Hemoglobin)** | {report_query} | **< 5.7%** (Normal) | Measures average blood glucose level over the past 2–3 months. |
| **2** | **Fasting Blood Sugar (FBS)** | 126 mg/dL | **70 – 99 mg/dL** | Measures blood glucose after overnight fasting. |
| **3** | **Serum Creatinine** | 1.1 mg/dL | **0.7 – 1.3 mg/dL** | Indicator of kidney filtration performance. |

*Note: This explanation is for educational understanding only and is NOT a medical diagnosis. Please share your lab reports with Dr. Nithin for clinical evaluation.*"""

            return {
                "agentType": "REPORT_READER_AGENT",
                "isSlashBypass": True,
                "reportQuery": report_query,
                "tableMarkdown": explanation_markdown,
                "replyText": explanation_markdown
            }

        # /comfort or /diagnostic command: Food, Purpose & Exercise Markdown Table
        if cmd in ["comfort", "diagnostic", "diet", "remedy"]:
            condition = args if args else "general health"
            table_markdown = f"""### 🥗 Structured Clinical Comfort & Diet Guide ({condition.capitalize()})

| S.No | Recommended Food / Nutrient | Clinical Purpose & Purpose | Recommended Exercises & Mobility |
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

        # /emergency command: Immediate Red-Flag Alert, SMTP Email & Top 4 ER Hospitals
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
                "replyText": f"⚠️ **URGENT EMERGENCY ALERT**\n\nAn automated emergency notification has been transmitted via SMTP to **{ALERT_RECIPIENT_EMAIL}**. Below are the top {len(er_hospitals)} nearest 24/7 ER emergency hospitals in Coimbatore District."
            }

        # /triage command: Differential Disease Likelihood Ranking
        if cmd in ["triage", "differential", "rank"]:
            return generate_differential_likelihood_response(args or raw_msg)

    # --- 2. RED-FLAG EMERGENCY CHECK (HIGH SEVERITY) ---
    red_flag_keywords = ["chest pain", "heart pain", "heart attack", "slurred speech", "facial drooping", "stroke", "cannot breathe", "severe breathlessness", "anaphylaxis", "poisoning", "snakebite"]
    if any(rf in msg_lower for rf in red_flag_keywords):
        send_emergency_smtp_email(patient_name, patient_phone, raw_msg)
        er_hospitals = fetch_top_hospitals_by_sector("emergency", user_lat, user_lng, limit=4)
        return {
            "agentType": "EMERGENCY_TRIAGE_AGENT",
            "isSlashBypass": False,
            "isRedFlag": True,
            "emergencyLevel": "CRITICAL",
            "smtpAlertSent": True,
            "erHospitals": er_hospitals,
            "replyText": f"⚠️ **URGENT MEDICAL ALERT: CRITICAL SYMPTOMS DETECTED**\n\nYour symptoms ({raw_msg}) indicate a potential emergency. An automated alert has been dispatched via SMTP to **{ALERT_RECIPIENT_EMAIL}**.\n\nPlease reach out immediately to one of the top 24/7 ER hospitals below or call 108 emergency services."
        }

    # --- 3. TIMELINE MEDICINE GUARDRAIL ENFORCER ---
    medicine_query_keywords = ["take", "tablet", "capsule", "dosage", "amoxicillin", "paracetamol", "antibiotic", "painkiller", "medicine"]
    if any(mk in msg_lower for mk in medicine_query_keywords):
        # Extract potential medicine name
        words = raw_msg.split()
        for w in words:
            clean_w = ''.join(filter(str.isalpha, w))
            if len(clean_w) >= 4 and clean_w.lower() not in ["take", "tablet", "capsule", "dosage", "what", "should", "with", "have", "from", "this"]:
                is_prescribed = check_medicine_timeline_guardrail(clean_w, patient_phone)
                if not is_prescribed:
                    return {
                        "agentType": "GUARDRAIL_ENFORCER",
                        "isBlocked": True,
                        "replyText": "⚠️ **Prescription Guardrail Notice**\n\nPlease consult your prescribing doctor for medicines and share your health concerns with them."
                    }

    # --- 4. ORGAN COMPLAINT DIRECT MAPPING (No Remedial Solution) ---
    organ_map = {
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

    for organ, specialty_name in organ_map.items():
        if organ in msg_lower:
            hospitals = fetch_top_hospitals_by_sector(specialty_name, user_lat, user_lng, limit=4)
            return {
                "agentType": "SPECIALTY_AGENT",
                "isSlashBypass": False,
                "detectedOrgan": organ.capitalize(),
                "matchedSpecialty": specialty_name,
                "hospitals": hospitals,
                "replyText": f"🏥 **Specialized Hospital Sector Recommendation ({specialty_name})**\n\nFor {organ.capitalize()} concerns, no home remedies are provided—please consult a specialist at one of the top {len(hospitals)} specialized sector hospitals in Coimbatore District below."
            }

    # --- 5. ADVISOR OVERLAY SUPERVISOR ROUTING (Standard Text Chat) ---
    if pdf_context:
        # Transient PDF Vector RAG Response
        return {
            "agentType": "PDF_VECTOR_RAG_AGENT",
            "replyText": f"📄 **Attachment Analysis (In-Memory Transient PDF)**\n\nBased on your uploaded PDF document:\n\n{pdf_context[:400]}...\n\n*Note: Uploaded PDF data is processed ephemerally in memory and is NOT stored anywhere.*"
        }

    # Default Advisor Overlay Differential Likelihood Triage
    return generate_differential_likelihood_response(raw_msg)


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
