import json
from typing import Dict, Any, List
from database import SessionLocal, PrescriptionDB, PatientDB

# Clinical Contraindication Matrix
CONTRAINDICATION_RULES = [
    {
        "group1": ["calpol", "paracetamol", "acetaminophen", "meftal", "mefenamic"],
        "group2": ["meftal", "ibuprofen", "naproxen", "combiflam"],
        "severity": "MEDIUM",
        "warning": "Dual NSAID / Analgesic Risk: Combining multiple fever/pain relievers increases gastric mucosal irritation. Space doses by at least 4 hours."
    },
    {
        "group1": ["aspirin", "warfarin", "clopidogrel", "heparin"],
        "group2": ["ibuprofen", "naproxen", "meftal", "diclofenac"],
        "severity": "HIGH",
        "warning": "Bleeding Risk Contraindication: NSAIDs combined with anticoagulants significantly elevate gastrointestinal bleeding risk."
    },
    {
        "group1": ["gelusil", "digene", "pantoprazole", "omeprazole", "antacid"],
        "group2": ["autrin", "ferrous", "iron", "calcium", "ciprofloxacin"],
        "severity": "MODERATE",
        "warning": "Absorption Inhibition Spacing: Antacids reduce iron/calcium absorption. Take antacids 2 hours before or after meals/supplements."
    }
]

def evaluate_drug_interactions(new_medications: List[Dict[str, Any]], patient_id: int) -> Dict[str, Any]:
    """
    Food & Drug Interaction Safety Agent:
    When a paper slip is scanned via OCR or Voice STT, cross-checks new medications
    against existing timeline records in SQLite, flagging interaction risks.
    """
    db = SessionLocal()
    try:
        patient = db.query(PatientDB).filter(
            (PatientDB.id == patient_id) | (PatientDB.phone_number == patient_id)
        ).first()

        real_pat_id = patient.id if patient else patient_id
        real_phone = patient.phone_number if patient else patient_id

        # Fetch existing active medications from SQLite
        existing_meds = []
        rxs = db.query(PrescriptionDB).filter(
            (PrescriptionDB.patient_id == real_pat_id) |
            (PrescriptionDB.patient_phone_number == real_phone)
        ).all()

        for rx in rxs:
            try:
                meds = json.loads(rx.medications_json) if rx.medications_json else []
                existing_meds.extend(meds)
            except Exception:
                pass

        all_med_names = [m.get("name", "").lower() for m in new_medications + existing_meds]
        warnings = []

        for rule in CONTRAINDICATION_RULES:
            match1 = any(g1 in name for g1 in rule["group1"] for name in all_med_names)
            match2 = any(g2 in name for g2 in rule["group2"] for name in all_med_names)

            if match1 and match2:
                warnings.append({
                    "severity": rule["severity"],
                    "warning": rule["warning"]
                })

        return {
            "has_interactions": len(warnings) > 0,
            "warnings_count": len(warnings),
            "warnings": warnings,
            "checked_medication_count": len(new_medications)
        }
    except Exception as e:
        print(f"[SafetyAgent Error]: {e}")
        return {"has_interactions": False, "error": str(e)}
    finally:
        db.close()
