import re
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db, PrescriptionDB
from auth import parse_phone_number
from graphs.timeline import generate_visit_summary, save_prescription_to_timeline, get_patient_timeline
from graphs.context_agent import build_patient_health_context
from repositories.prescription_repository import PrescriptionRepository

router = APIRouter(prefix="/api/timeline", tags=["Timeline & Prescriptions"])

def get_rx_repo(db: Session = Depends(get_db)) -> PrescriptionRepository:
    return PrescriptionRepository(db)


@router.post("/save")
def timeline_save_endpoint(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    Saves a confirmed prescription into SQLite database, generating a narrative Visit Summary.
    """
    try:
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

        meds_data = body.get("medications", [])
        dietary_data = dietary

        new_rx = PrescriptionDB(
            id=rx_id,
            patient_id=patient_id_num,
            doctor_id=payload.get("doctorId", 500001),
            source=payload.get("source", "doctor_voice"),
            patient_name=payload.get("patientName", "Patient"),
            patient_country_code=pat_cc,
            patient_phone_number=pat_phone_num,
            doctor_name=header.get("doctorName", "Dr. Prescribing Doctor"),
            hospital_name=header.get("hospitalName", "Coimbatore Health Centre"),
            recorded_diagnosis=body.get("recordedDiagnosis", ""),
            medications_json=meds_data,
            dietary_advice_json=dietary_data,
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


@router.get("/{patient_id}")
def timeline_get_endpoint(
    patient_id: str,
    doctor_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns timeline entries for a patient.
    If doctor_id is provided: scoped to that doctor.
    If doctor_id is None: returns full longitudinal record.
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
        meds = rx.medications_json if isinstance(rx.medications_json, list) else []
        if isinstance(rx.medications_json, str):
            try:
                meds = json.loads(rx.medications_json)
            except Exception:
                meds = []

        dietary = rx.dietary_advice_json if isinstance(rx.dietary_advice_json, (dict, list)) else {}
        if isinstance(rx.dietary_advice_json, str):
            try:
                dietary = json.loads(rx.dietary_advice_json)
            except Exception:
                dietary = {}

        results.append({
            "id": rx.id,
            "patientId": str(rx.patient_id),
            "patientName": rx.patient_name,
            "patientPhone": f"{rx.patient_country_code}{rx.patient_phone_number}",
            "countryCode": rx.patient_country_code,
            "phoneNumber": rx.patient_phone_number,
            "date": rx.created_at.strftime("%Y-%m-%d") if rx.created_at else "",
            "time": rx.created_at.strftime("%H:%M") if rx.created_at else "",
            "index": idx,
            "visitSummary": rx.visit_summary,
            "source": rx.source,
            "header": {
                "doctorName": rx.doctor_name,
                "hospitalName": rx.hospital_name,
                "opdContact": "",
                "date": rx.created_at.strftime("%Y-%m-%d") if rx.created_at else ""
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

    if not results:
        results = get_patient_timeline(patient_id)

    return {"patientId": patient_id, "prescriptions": results}


@router.get("/context/{patient_id}")
def timeline_context_endpoint(patient_id: str):
    """
    Returns enriched patient clinical context generated by Timeline Context Agent.
    """
    return build_patient_health_context(patient_id)
