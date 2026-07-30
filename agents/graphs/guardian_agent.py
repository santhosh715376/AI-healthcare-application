import os
from typing import Dict, Any, Optional
from datetime import datetime
from database import SessionLocal, AdherenceLogDB, AdherenceScheduleDB, PatientDB

def check_consecutive_missed_doses(patient_id: int) -> Dict[str, Any]:
    """
    Proactive Adherence Guardian Agent:
    Monitors SQLite adherence_logs. If a patient misses 2 consecutive dose windows,
    autonomously triggers an AI intervention prompt.
    """
    db = SessionLocal()
    try:
        patient = db.query(PatientDB).filter(
            (PatientDB.id == patient_id) | (PatientDB.phone_number == patient_id)
        ).first()

        pat_name = patient.name if patient else "Patient"
        pat_id_clean = patient.id if patient else patient_id

        # Query recent logs sorted by creation / date desc
        logs = db.query(AdherenceLogDB).filter(
            AdherenceLogDB.patient_id == pat_id_clean
        ).order_by(AdherenceLogDB.created_at.desc()).limit(5).all()

        missed_count = 0
        last_missed_med = ""
        last_missed_slot = ""

        for log in logs:
            if log.status == "MISSED" or log.status == "DUE":
                missed_count += 1
                if not last_missed_med:
                    last_missed_med = log.medication_name
                    last_missed_slot = log.routine_slot
            else:
                break  # Reset consecutive count if a dose was TAKEN

        if missed_count >= 2:
            return {
                "intervention_required": True,
                "missed_count": missed_count,
                "medication_name": last_missed_med or "prescribed medication",
                "routine_slot": last_missed_slot or "recent",
                "patient_name": pat_name,
                "banner_msg": f"Hi {pat_name}, we noticed you missed your {last_missed_slot} dose of {last_missed_med}. Are you feeling nauseous or experiencing side effects?",
                "action_prompt": "Would you like me to connect you with your prescribing doctor or adjust your dose schedule?"
            }
        
        return {
            "intervention_required": False,
            "missed_count": missed_count,
            "patient_name": pat_name
        }
    except Exception as e:
        print(f"[GuardianAgent Error]: {e}")
        return {"intervention_required": False, "error": str(e)}
    finally:
        db.close()
