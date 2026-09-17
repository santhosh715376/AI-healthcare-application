from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from database import AdherenceScheduleDB, AdherenceLogDB
from repositories.base import BaseRepository

class AdherenceRepository(BaseRepository[AdherenceScheduleDB]):
    """
    Repository managing Medication Adherence Schedules and Daily Check-In Logs.
    Implements clean CRUD operations and status queries.
    """
    def __init__(self, db: Session):
        super().__init__(db, AdherenceScheduleDB)

    def get_schedules_by_patient(self, patient_id: int) -> List[AdherenceScheduleDB]:
        """Fetch all active adherence schedules for a patient."""
        return self.db.query(AdherenceScheduleDB).filter(AdherenceScheduleDB.patient_id == patient_id).all()

    def get_log(self, schedule_id: int, date_str: str, slot: str) -> Optional[AdherenceLogDB]:
        """Fetch check-in log for a specific schedule, date, and routine slot."""
        return (
            self.db.query(AdherenceLogDB)
            .filter(
                AdherenceLogDB.schedule_id == schedule_id,
                AdherenceLogDB.scheduled_date == date_str,
                AdherenceLogDB.routine_slot == slot
            )
            .first()
        )

    def get_today_logs_for_patient(self, patient_id: int, date_str: str) -> List[AdherenceLogDB]:
        """Fetch all logs for a patient on a specific date."""
        return (
            self.db.query(AdherenceLogDB)
            .filter(
                AdherenceLogDB.patient_id == patient_id,
                AdherenceLogDB.scheduled_date == date_str
            )
            .all()
        )

    def upsert_checkin(
        self,
        schedule_id: int,
        patient_id: int,
        date_str: str,
        slot: str,
        status: str,
        medication_name: Optional[str] = None
    ) -> AdherenceLogDB:
        """Upsert a check-in action (TAKEN, MISSED, SKIPPED)."""
        log = self.get_log(schedule_id, date_str, slot)
        now = datetime.utcnow()

        if not log:
            if not medication_name:
                sched = self.get_by_id(schedule_id)
                medication_name = sched.medication_name if sched else "Prescribed Medicine"

            log = AdherenceLogDB(
                schedule_id=schedule_id,
                patient_id=patient_id,
                medication_name=medication_name,
                scheduled_date=date_str,
                routine_slot=slot,
                status=status,
                check_in_timestamp=now
            )
            self.db.add(log)
        else:
            log.status = status
            log.check_in_timestamp = now

        self.db.commit()
        self.db.refresh(log)
        return log
