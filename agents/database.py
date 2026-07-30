import os
import sys
import importlib.util

# Load Primary System Data Layer directly from d:\health_care\database.py using importlib
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_db_path = os.path.join(ROOT_DIR, "database.py")

spec = importlib.util.spec_from_file_location("primary_database", root_db_path)
primary_db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(primary_db)

# Re-export all symbols for backward compatibility
engine = primary_db.engine
SessionLocal = primary_db.SessionLocal
Base = primary_db.Base
init_db = primary_db.init_db
get_db = primary_db.get_db
DoctorDB = primary_db.DoctorDB
PatientDB = primary_db.PatientDB
DependentDB = primary_db.DependentDB
ConsentGrantDB = primary_db.ConsentGrantDB
PrescriptionDB = primary_db.PrescriptionDB
HospitalDB = primary_db.HospitalDB
AdherenceScheduleDB = primary_db.AdherenceScheduleDB
AdherenceLogDB = primary_db.AdherenceLogDB

if __name__ == "__main__":
    init_db()
