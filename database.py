import os
import json
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, Text,
    DateTime, ForeignKey, BigInteger, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

# Primary System Database Location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "healthcare.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Enable SQLite Write-Ahead Logging (WAL) and busy_timeout
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DoctorDB(Base):
    __tablename__ = "doctors"

    sno = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    country_code = Column(String, nullable=False, default="+91")
    phone_number = Column(BigInteger, nullable=False, index=True)  # 10-digit integer
    password_hash = Column(String, nullable=False)
    gender = Column(String, nullable=True, default="Male")
    age = Column(Integer, nullable=True, default=35)
    height_cm = Column(Float, nullable=True, default=175.0)
    weight_kg = Column(Float, nullable=True, default=70.0)
    blood_group = Column(String, nullable=True, default="O+")
    doc_license = Column(String, unique=True, nullable=False, index=True)  # NMC License ID
    hospital_name = Column(String, nullable=False)
    specialty = Column(String, nullable=False, default="General Medicine")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("country_code", "phone_number", name="uq_doctor_phone"),
        CheckConstraint("phone_number BETWEEN 1000000000 AND 9999999999", name="check_doctor_phone_10digits")
    )


class PatientDB(Base):
    __tablename__ = "patients"

    sno = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    country_code = Column(String, nullable=False, default="+91")
    phone_number = Column(BigInteger, nullable=False, index=True)  # 10-digit integer
    password_hash = Column(String, nullable=False)
    
    # CLINICAL VITALS
    age = Column(Integer, nullable=True, default=24)
    gender = Column(String, nullable=True, default="Male")
    height_cm = Column(Float, nullable=True, default=175.0)
    weight_kg = Column(Float, nullable=True, default=68.0)
    blood_group = Column(String, nullable=True, default="O+")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("country_code", "phone_number", name="uq_patient_phone"),
        CheckConstraint("phone_number BETWEEN 1000000000 AND 9999999999", name="check_patient_phone_10digits")
    )


class DependentDB(Base):
    __tablename__ = "dependents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    primary_patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    dependent_name = Column(String, nullable=False)
    relationship = Column(String, nullable=False)  # 'father' | 'mother' | 'son' | 'daughter' | 'spouse' | 'other'
    age = Column(Integer, nullable=True)
    accessibility_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConsentGrantDB(Base):
    __tablename__ = "consent_grants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_phone_number = Column(BigInteger, nullable=False, index=True)
    doctor_license = Column(String, nullable=False, index=True)
    scope = Column(String, nullable=False, default="full")  # 'full' | 'meds_only' | 'nothing'
    granted_at = Column(DateTime, default=datetime.utcnow)


class PrescriptionDB(Base):
    __tablename__ = "prescriptions"

    sno = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String, unique=True, nullable=False, index=True)  # rx-100001
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True, index=True)
    dependent_id = Column(Integer, ForeignKey("dependents.id"), nullable=True, index=True)
    source = Column(String, nullable=False, default="doctor_voice")  # 'doctor_voice' | 'doctor_ocr' | 'patient_ocr'
    
    patient_name = Column(String, nullable=False)
    patient_country_code = Column(String, default="+91")
    patient_phone_number = Column(BigInteger, nullable=False)

    doctor_name = Column(String, nullable=False)
    hospital_name = Column(String, nullable=False)
    
    recorded_diagnosis = Column(Text, nullable=False)
    medications_json = Column(Text, nullable=False)  # Validated JSON string array
    dietary_advice_json = Column(Text, nullable=True)
    advice = Column(Text, nullable=True)
    follow_up_date = Column(String, nullable=True)
    visit_summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class HospitalDB(Base):
    __tablename__ = "hospitals"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    beds = Column(Integer, default=150)
    category = Column(String, default="Multispecialty Hospital")
    specialties = Column(Text, default="General Medicine, Emergency Care")
    emergency_specialty_24x7 = Column(Text, default="24/7 Emergency & General Medicine")
    facilities_json = Column(Text, default='["24/7 Emergency", "ICU", "Pharmacy"]')
    best_sector = Column(Text, default="General Multispecialty")
    rating = Column(Float, default=4.5)
    review_count = Column(Integer, default=150)
    emergency_24x7 = Column(Boolean, default=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    review_snippet = Column(Text, nullable=True)


class AdherenceScheduleDB(Base):
    __tablename__ = "adherence_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prescription_id = Column(String, ForeignKey("prescriptions.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    dependent_id = Column(Integer, ForeignKey("dependents.id"), nullable=True)
    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=True)
    food_relation = Column(String, nullable=False, default="After Food")
    routine_slot = Column(String, nullable=False, default="morning")
    slot_start_time = Column(String, nullable=False, default="08:00")
    slot_end_time = Column(String, nullable=False, default="08:30")
    duration_days = Column(Integer, nullable=False, default=5)
    total_doses_expected = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)


class AdherenceLogDB(Base):
    __tablename__ = "adherence_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey("adherence_schedules.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    medication_name = Column(String, nullable=False)
    scheduled_date = Column(String, nullable=False, index=True)
    routine_slot = Column(String, nullable=False)
    status = Column(String, nullable=False, default="DUE")
    check_in_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def seed_hospitals_if_empty():
    db = SessionLocal()
    try:
        count = db.query(HospitalDB).count()
        if count > 0:
            return

        district_hospitals = [
            {
                "id": "hosp_1001",
                "name": "Kovai Medical Center and Hospital (KMCH)",
                "lat": 11.0424, "lon": 77.0378, "beds": 750,
                "cat": "Super Specialty Hospital",
                "spec": "Cardiology, Trauma, Neurosurgery, Oncology, Emergency Medicine",
                "em_spec": "24/7 Level-1 Trauma & Emergency ICU",
                "facilities": ["24/7 Level-1 Trauma", "Cardiac Cath Lab", "Pediatric ICU", "Helipad"],
                "best_sec": "Best Sector: Comprehensive Emergency & Cardiac Care",
                "rating": 4.8, "reviews": 4250,
                "phone": "+91 422 4323800", "addr": "Avinashi Road, Civil Aerodrome Post, Coimbatore"
            },
            {
                "id": "hosp_1002",
                "name": "Sri Ramakrishna Hospital",
                "lat": 11.0168, "lon": 76.9558, "beds": 600,
                "cat": "Multispecialty Hospital",
                "spec": "Cardiology, Pediatrics, Orthopedics, Nephrology",
                "em_spec": "24/7 Emergency & Pediatric ICU",
                "facilities": ["24/7 Emergency", "Pediatric ICU", "Dialysis Unit"],
                "best_sec": "Best Sector: Pediatric & Multi-Specialty Care",
                "rating": 4.7, "reviews": 3100,
                "phone": "+91 422 4500000", "addr": "Siddhapudur, Coimbatore"
            },
            {
                "id": "hosp_1003",
                "name": "Ganga Hospital",
                "lat": 11.0195, "lon": 76.9512, "beds": 500,
                "cat": "Specialty Trauma Center",
                "spec": "Orthopedics, Trauma, Plastic Surgery, Reconstructive Surgery",
                "em_spec": "24/7 Orthopedic Trauma & Burn ICU",
                "facilities": ["24/7 Trauma Surgery", "Plastic Surgery OT", "Rehabilitation"],
                "best_sec": "Best Sector: Orthopedic Trauma & Plastic Surgery",
                "rating": 4.9, "reviews": 5800,
                "phone": "+91 422 2485000", "addr": "313 Mettupalayam Road, Coimbatore"
            },
            {
                "id": "hosp_1004",
                "name": "PSG Hospitals",
                "lat": 11.0289, "lon": 77.0031, "beds": 650,
                "cat": "Teaching Super Specialty",
                "spec": "General Medicine, Cardiology, Neurology, Gastroenterology",
                "em_spec": "24/7 Critical Care & Stroke Unit",
                "facilities": ["Stroke Unit", "24/7 Emergency", "Blood Bank", "MRI/CT"],
                "best_sec": "Best Sector: Neurology & Multi-Specialty ICU",
                "rating": 4.7, "reviews": 3900,
                "phone": "+91 422 2570170", "addr": "Peelamedu, Coimbatore"
            }
        ]

        seed_records = []
        for item in district_hospitals:
            h_obj = HospitalDB(
                id=item["id"],
                name=item["name"],
                latitude=item["lat"],
                longitude=item["lon"],
                beds=item["beds"],
                category=item["cat"],
                specialties=item["spec"],
                emergency_specialty_24x7=item["em_spec"],
                facilities_json=json.dumps(item["facilities"]),
                best_sector=item["best_sec"],
                rating=item["rating"],
                review_count=item["reviews"],
                emergency_24x7=True,
                phone=item["phone"],
                address=item["addr"],
                review_snippet="Immediate 24/7 emergency response, modern facilities, and expert physicians."
            )
            seed_records.append(h_obj)

        db.add_all(seed_records)
        db.commit()
        print(f"[Database] Seeded {len(seed_records)} primary hospital spatial records into SQLite.")
    except Exception as e:
        db.rollback()
        print(f"[Database] Error seeding hospital records: {e}")
    finally:
        db.close()


def init_db():
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        if inspector.has_table("doctors"):
            doc_cols = [c["name"] for c in inspector.get_columns("doctors")]
            if "specialty" not in doc_cols:
                conn.execute(text("ALTER TABLE doctors ADD COLUMN specialty TEXT NOT NULL DEFAULT 'General Medicine'"))
            if "gender" not in doc_cols:
                conn.execute(text("ALTER TABLE doctors ADD COLUMN gender TEXT DEFAULT 'Male'"))
            if "age" not in doc_cols:
                conn.execute(text("ALTER TABLE doctors ADD COLUMN age INTEGER DEFAULT 35"))
                conn.execute(text("ALTER TABLE doctors ADD COLUMN height_cm REAL DEFAULT 175.0"))
                conn.execute(text("ALTER TABLE doctors ADD COLUMN weight_kg REAL DEFAULT 70.0"))
                conn.execute(text("ALTER TABLE doctors ADD COLUMN blood_group TEXT DEFAULT 'O+'"))
            conn.commit()

        if inspector.has_table("patients"):
            pat_cols = [c["name"] for c in inspector.get_columns("patients")]
            if "age" not in pat_cols:
                conn.execute(text("ALTER TABLE patients ADD COLUMN age INTEGER DEFAULT 24"))
                conn.execute(text("ALTER TABLE patients ADD COLUMN gender TEXT DEFAULT 'Male'"))
                conn.execute(text("ALTER TABLE patients ADD COLUMN height_cm REAL DEFAULT 175.0"))
                conn.execute(text("ALTER TABLE patients ADD COLUMN weight_kg REAL DEFAULT 68.0"))
                conn.execute(text("ALTER TABLE patients ADD COLUMN blood_group TEXT DEFAULT 'O+'"))
                conn.commit()

    Base.metadata.create_all(bind=engine)
    seed_hospitals_if_empty()
    print(f"[Primary Database] SQLite initialized with WAL mode at: {DB_PATH}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
