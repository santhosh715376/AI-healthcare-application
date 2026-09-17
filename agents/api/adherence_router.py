import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, PatientDB, PrescriptionDB, AdherenceScheduleDB, AdherenceLogDB
from auth import parse_phone_number, require_patient
from repositories.adherence_repository import AdherenceRepository

router = APIRouter(prefix="/api/adherence", tags=["Adherence & Routine Engine"])

def get_adh_repo(db: Session = Depends(get_db)) -> AdherenceRepository:
    return AdherenceRepository(db)


class SlotInfo(BaseModel):
    routine_slot: str
    slot_start_time: str
    slot_end_time: str

class CreateScheduleRequest(BaseModel):
    prescription_id: str
    patient_id: int
    medication_name: str
    dosage: Optional[str] = "1 tablet"
    food_relation: str = "After Food"
    duration_days: int = 5
    slots: List[SlotInfo]

class AdherenceCheckinRequest(BaseModel):
    schedule_id: int
    patient_id: int
    routine_slot: str
    scheduled_date: str


@router.post("/schedule")
def create_adherence_schedule_endpoint(
    payload: CreateScheduleRequest,
    db: Session = Depends(get_db),
    repo: AdherenceRepository = Depends(get_adh_repo)
):
    """
    Creates dynamic user-configured adherence schedules and check-in logs.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    created_schedules = []

    pat_param = payload.patient_id
    patient = db.query(PatientDB).filter(
        (PatientDB.id == pat_param) | (PatientDB.phone_number == pat_param)
    ).first()

    real_pat_id = patient.id if patient else pat_param
    real_phone_num = patient.phone_number if patient else pat_param

    for slot in payload.slots:
        existing = db.query(AdherenceScheduleDB).filter(
            AdherenceScheduleDB.prescription_id == payload.prescription_id,
            (AdherenceScheduleDB.patient_id == real_pat_id) | (AdherenceScheduleDB.patient_id == real_phone_num),
            AdherenceScheduleDB.medication_name == payload.medication_name,
            AdherenceScheduleDB.routine_slot == slot.routine_slot
        ).first()

        if existing:
            existing.patient_id = real_pat_id
            existing.slot_start_time = slot.slot_start_time
            existing.slot_end_time = slot.slot_end_time
            existing.food_relation = payload.food_relation
            existing.duration_days = payload.duration_days
            sched = existing
        else:
            sched = AdherenceScheduleDB(
                prescription_id=payload.prescription_id,
                patient_id=real_pat_id,
                medication_name=payload.medication_name,
                dosage=payload.dosage or "",
                food_relation=payload.food_relation,
                routine_slot=slot.routine_slot,
                slot_start_time=slot.slot_start_time,
                slot_end_time=slot.slot_end_time,
                duration_days=payload.duration_days,
                total_doses_expected=payload.duration_days
            )
            db.add(sched)
            db.flush()

        log_entry = db.query(AdherenceLogDB).filter(
            AdherenceLogDB.schedule_id == sched.id,
            (AdherenceLogDB.patient_id == real_pat_id) | (AdherenceLogDB.patient_id == real_phone_num),
            AdherenceLogDB.scheduled_date == today_str,
            AdherenceLogDB.routine_slot == slot.routine_slot
        ).first()

        if not log_entry:
            log_entry = AdherenceLogDB(
                schedule_id=sched.id,
                patient_id=real_pat_id,
                medication_name=payload.medication_name,
                scheduled_date=today_str,
                routine_slot=slot.routine_slot,
                status="DUE"
            )
            db.add(log_entry)
        else:
            log_entry.patient_id = real_pat_id

        created_schedules.append({
            "schedule_id": sched.id,
            "medication_name": sched.medication_name,
            "routine_slot": sched.routine_slot,
            "slot_start_time": sched.slot_start_time,
            "slot_end_time": sched.slot_end_time,
            "food_relation": sched.food_relation
        })

    db.commit()
    return {
        "status": "success",
        "message": "Adherence schedule & check-in log saved successfully.",
        "schedules": created_schedules
    }


@router.get("/patient/{patient_id}")
def get_patient_adherence_endpoint(
    patient_id: str,
    db: Session = Depends(get_db),
    repo: AdherenceRepository = Depends(get_adh_repo)
):
    """
    Returns active adherence schedules and today's check-in status aggregated across ALL active prescriptions for a patient.
    """
    query_clean = str(patient_id).strip()
    try:
        patient_num = int(query_clean.replace("pat-", ""))
    except Exception:
        patient_num = 100001

    try:
        _, parsed_num = parse_phone_number(query_clean)
    except Exception:
        try:
            parsed_num = int(re.sub(r"\D", "", query_clean))
        except Exception:
            parsed_num = -1

    patient = db.query(PatientDB).filter(
        (PatientDB.id == patient_num) | 
        (PatientDB.phone_number == parsed_num) |
        (PatientDB.id == parsed_num)
    ).first()

    real_pat_id = patient.id if patient else patient_num
    real_phone_num = patient.phone_number if patient else parsed_num
    today_str = datetime.now().strftime("%Y-%m-%d")

    schedules = db.query(AdherenceScheduleDB).filter(
        (AdherenceScheduleDB.patient_id == real_pat_id) |
        (AdherenceScheduleDB.patient_id == real_phone_num)
    ).all()

    rx_map = {}
    rxs = db.query(PrescriptionDB).filter(
        (PrescriptionDB.patient_id == real_pat_id) |
        (PrescriptionDB.patient_phone_number == real_phone_num)
    ).all()
    for rx in rxs:
        rx_map[rx.id] = {
            "doctor_name": rx.doctor_name,
            "hospital_name": rx.hospital_name,
            "date": rx.created_at.strftime("%b %d") if rx.created_at else "Recent"
        }

    formatted_slots = {"morning": [], "noon": [], "night": []}
    total_expected = 0
    total_taken = 0

    for sched in schedules:
        total_expected += 1
        rx_info = rx_map.get(sched.prescription_id, {"doctor_name": "Dr. Prescribing Doctor", "date": "Recent"})

        log = repo.get_log(sched.id, today_str, sched.routine_slot)

        status = log.status if log else "DUE"
        if status == "TAKEN":
            total_taken += 1

        slot_key = sched.routine_slot.lower()
        if slot_key not in formatted_slots:
            slot_key = "morning"

        formatted_slots[slot_key].append({
            "schedule_id": sched.id,
            "prescription_id": sched.prescription_id,
            "medication_name": sched.medication_name,
            "dosage": sched.dosage,
            "food_relation": sched.food_relation,
            "routine_slot": sched.routine_slot,
            "slot_start_time": sched.slot_start_time,
            "slot_end_time": sched.slot_end_time,
            "doctor_name": rx_info["doctor_name"],
            "visit_date": rx_info["date"],
            "status": status,
            "scheduled_date": today_str
        })

    adherence_pct = int((total_taken / total_expected * 100)) if total_expected > 0 else 100

    return {
        "status": "success",
        "patient_id": real_pat_id,
        "master_adherence_pct": adherence_pct,
        "total_taken": total_taken,
        "total_expected": total_expected,
        "slots": formatted_slots
    }


@router.post("/checkin")
def checkin_dose_endpoint(
    payload: AdherenceCheckinRequest,
    repo: AdherenceRepository = Depends(get_adh_repo)
):
    """
    Submits a dose check-in log. Uses AdherenceRepository for persistence.
    """
    log = repo.upsert_checkin(
        schedule_id=payload.schedule_id,
        patient_id=payload.patient_id,
        date_str=payload.scheduled_date,
        slot=payload.routine_slot,
        status="TAKEN"
    )

    return {
        "status": "success",
        "message": "Dose check-in recorded successfully.",
        "log_id": log.id,
        "current_status": log.status
    }
