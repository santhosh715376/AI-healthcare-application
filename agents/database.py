import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_PATH = os.path.join(os.path.dirname(__file__), "healthcare.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
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
    doc_license = Column(String, unique=True, nullable=False, index=True)  # NMC License ID
    hospital_name = Column(String, nullable=False)
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
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("country_code", "phone_number", name="uq_patient_phone"),
        CheckConstraint("phone_number BETWEEN 1000000000 AND 9999999999", name="check_patient_phone_10digits")
    )


class PrescriptionDB(Base):
    __tablename__ = "prescriptions"

    id = Column(String, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True, index=True)
    source = Column(String, nullable=False)  # 'doctor_voice' | 'doctor_ocr' | 'patient_ocr'
    patient_name = Column(String, nullable=False)
    patient_country_code = Column(String, nullable=False, default="+91")
    patient_phone_number = Column(BigInteger, nullable=False, index=True)
    doctor_name = Column(String, nullable=False)
    hospital_name = Column(String, nullable=False)
    recorded_diagnosis = Column(Text, nullable=True)
    medications_json = Column(Text, nullable=False)      # JSON array of meds
    dietary_advice_json = Column(Text, nullable=True)   # JSON object of foods & remedies
    advice = Column(Text, nullable=True)
    follow_up_date = Column(String, nullable=True)
    visit_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    print(f"[Database] SQLite initialized with country_code & BIGINT 10-digit phone_number at: {DB_PATH}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
