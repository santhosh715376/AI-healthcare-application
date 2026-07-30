from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from database import SessionLocal, AdherenceLogDB, AdherenceScheduleDB, PatientDB

def analyze_routine_drift(patient_id: int) -> Dict[str, Any]:
    """
    Dynamic Routine Optimizer Agent:
    Learns the patient's real-world check-in timestamp patterns over 14 days
    and suggests optimal schedule adjustments aligned with sleep/meal habits.
    """
    db = SessionLocal()
    try:
        patient = db.query(PatientDB).filter(
            (PatientDB.id == patient_id) | (PatientDB.phone_number == patient_id)
        ).first()

        real_pat_id = patient.id if patient else patient_id

        # Fetch active schedules
        schedules = db.query(AdherenceScheduleDB).filter(AdherenceScheduleDB.patient_id == real_pat_id).all()
        if not schedules:
            return {"suggestion_available": False, "reason": "No active schedules configured."}

        # Analyze check-in logs with actual check_in_timestamp
        logs = db.query(AdherenceLogDB).filter(
            AdherenceLogDB.patient_id == real_pat_id,
            AdherenceLogDB.status == "TAKEN"
        ).order_by(AdherenceLogDB.check_in_timestamp.desc()).limit(14).all()

        if len(logs) < 3:
            return {"suggestion_available": False, "reason": "Insufficient check-in history (<3 check-ins)."}

        # Calculate morning drift offset
        morning_offsets = []
        for log in logs:
            if log.routine_slot == "morning" and log.check_in_timestamp:
                check_in_min = log.check_in_timestamp.hour * 60 + log.check_in_timestamp.minute
                assigned_min = 8 * 60  # 08:00 AM standard
                morning_offsets.append(check_in_min - assigned_min)

        if morning_offsets and len(morning_offsets) >= 2:
            avg_drift_min = int(sum(morning_offsets) / len(morning_offsets))
            if avg_drift_min >= 30:
                suggested_start = f"{(8 + avg_drift_min // 60):02d}:{(avg_drift_min % 60):02d}"
                suggested_end = f"{(8 + (avg_drift_min + 30) // 60):02d}:{((avg_drift_min + 30) % 60):02d}"

                return {
                    "suggestion_available": True,
                    "slot": "morning",
                    "avg_drift_minutes": avg_drift_min,
                    "current_window": "08:00 - 08:30 AM",
                    "suggested_window": f"{suggested_start} - {suggested_end} AM",
                    "message": f"We noticed you usually check in your morning doses at {suggested_start} AM. Would you like to adjust your morning window to {suggested_start} - {suggested_end} AM to match your natural routine?"
                }

        return {"suggestion_available": False, "reason": "Current schedule perfectly matches your habits."}

    except Exception as e:
        print(f"[OptimizerAgent Error]: {e}")
        return {"suggestion_available": False, "error": str(e)}
    finally:
        db.close()
