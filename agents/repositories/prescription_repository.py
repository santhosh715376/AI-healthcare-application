from typing import Optional, List
from sqlalchemy.orm import Session
from database import PrescriptionDB
from repositories.base import BaseRepository

class PrescriptionRepository(BaseRepository[PrescriptionDB]):
    """
    Repository for Prescriptions and Longitudinal Patient Timeline Records.
    Adheres to Interface Segregation & Single Responsibility Principles.
    """
    def __init__(self, db: Session):
        super().__init__(db, PrescriptionDB)

    def get_latest_by_phone(self, phone: int) -> Optional[PrescriptionDB]:
        """Returns the most recent prescription record matching a 10-digit phone number."""
        clean_phone = int(str(phone)[-10:])
        return (
            self.db.query(PrescriptionDB)
            .filter(PrescriptionDB.patient_phone_number == clean_phone)
            .order_by(PrescriptionDB.created_at.desc())
            .first()
        )

    def get_all_by_phone(self, phone: int) -> List[PrescriptionDB]:
        """Returns all prescriptions for a patient phone number ordered newest first."""
        clean_phone = int(str(phone)[-10:])
        return (
            self.db.query(PrescriptionDB)
            .filter(PrescriptionDB.patient_phone_number == clean_phone)
            .order_by(PrescriptionDB.created_at.desc())
            .all()
        )

    def get_all_by_patient_id(self, patient_id: int) -> List[PrescriptionDB]:
        """Returns all prescriptions for a patient ID, sorted newest first."""
        return (
            self.db.query(PrescriptionDB)
            .filter(PrescriptionDB.patient_id == patient_id)
            .order_by(PrescriptionDB.created_at.desc())
            .all()
        )

    def get_timeline_scoped(self, patient_id: int, doctor_id: Optional[int] = None) -> List[PrescriptionDB]:
        """Scoped timeline query: allows doctor-specific filtering if requested."""
        q = self.db.query(PrescriptionDB).filter(PrescriptionDB.patient_id == patient_id)
        if doctor_id:
            q = q.filter(PrescriptionDB.doctor_id == doctor_id)
        return q.order_by(PrescriptionDB.created_at.desc()).all()
