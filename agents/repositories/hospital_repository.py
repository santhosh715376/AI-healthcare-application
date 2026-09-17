from typing import Optional, List
from sqlalchemy.orm import Session
from database import HospitalDB
from repositories.base import BaseRepository

class HospitalRepository(BaseRepository[HospitalDB]):
    """
    Repository for Geospatial Hospital Directory and Emergency Facilities.
    """
    def __init__(self, db: Session):
        super().__init__(db, HospitalDB)

    def find_emergency_24x7(self) -> List[HospitalDB]:
        """Fetch all hospitals offering 24/7 emergency response."""
        return self.db.query(HospitalDB).filter(HospitalDB.emergency_24x7 == True).all()

    def find_by_specialty(self, keyword: str) -> List[HospitalDB]:
        """Fetch hospitals matching a specialty or sector keyword."""
        kw = keyword.lower().strip()
        all_hosp = self.db.query(HospitalDB).all()
        return [
            h for h in all_hosp
            if kw in f"{h.name} {h.category} {h.specialties} {h.emergency_specialty_24x7} {h.best_sector}".lower()
        ]
