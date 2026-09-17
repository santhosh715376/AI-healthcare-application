import os
import sys
import importlib.util
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_db_path = os.path.join(ROOT_DIR, "database.py")

# Ensure single shared primary_database module in sys.modules
if "primary_database" not in sys.modules:
    spec = importlib.util.spec_from_file_location("primary_database", root_db_path)
    primary_db = importlib.util.module_from_spec(spec)
    sys.modules["primary_database"] = primary_db
    spec.loader.exec_module(primary_db)
else:
    primary_db = sys.modules["primary_database"]

DB_PATH = getattr(primary_db, "DB_PATH", os.environ.get(
    "HEALTHCARE_DB_PATH",
    os.path.join(ROOT_DIR, "clinical_platform.db")
))

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
JSONType = getattr(primary_db, "JSONType", None)

if __name__ == "__main__":
    init_db()
