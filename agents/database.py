import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, BigInteger, Float, Boolean, String, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
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


class HospitalDB(Base):
    __tablename__ = "hospitals"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    beds = Column(Integer, default=150)
    emergency_specialty_24x7 = Column(Text, default="24/7 Emergency & General Medicine")
    best_sector = Column(Text, default="General Multispecialty")
    rating = Column(Float, default=4.5)
    review_count = Column(Integer, default=150)
    category = Column(String, default="Multispecialty Hospital")
    specialties = Column(Text, default="General Medicine, Emergency Care")
    emergency_24x7 = Column(Boolean, default=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    review_snippet = Column(Text, nullable=True)


def seed_hospitals_if_empty():
    db = SessionLocal()
    try:
        # Re-seed to ensure full district coverage
        db.query(HospitalDB).delete()
        db.commit()

        district_hospitals = [
            # Central Coimbatore City
            {
                "id": "hosp_1001",
                "name": "Kovai Medical Center and Hospital (KMCH)",
                "lat": 11.0424, "lon": 77.0378, "beds": 750,
                "em_spec": "24/7 Cardiology, Trauma & Organ Transplant ICU",
                "best_sec": "Best Sector: Cardiac Surgery & Interventional Cardiology",
                "rating": 4.8, "reviews": 5120, "cat": "Super Specialty Hospital",
                "spec": "Cardiology, Trauma, Neurology, Oncology",
                "phone": "+91 422 4323800", "addr": "Avinashi Road, Peelamedu, Coimbatore"
            },
            {
                "id": "hosp_1002",
                "name": "Sri Ramakrishna Hospital",
                "lat": 11.0168, "lon": 76.9558, "beds": 550,
                "em_spec": "24/7 Pediatric ICU & Neonatal Emergency",
                "best_sec": "Best Sector: Pediatrics & Oncology",
                "rating": 4.7, "reviews": 4234, "cat": "Multispecialty Hospital",
                "spec": "Pediatrics, Oncology, Nephrology, Surgery",
                "phone": "+91 422 4500000", "addr": "395, Sarojini Naidu Rd, Sidhapudur, Coimbatore"
            },
            {
                "id": "hosp_1003",
                "name": "PSG Hospitals",
                "lat": 11.0289, "lon": 77.0031, "beds": 900,
                "em_spec": "24/7 Polytrauma & Neurosurgery ICU",
                "best_sec": "Best Sector: Polytrauma & Neurological Sciences",
                "rating": 4.9, "reviews": 6890, "cat": "Teaching & Super Specialty Hospital",
                "spec": "Neurosurgery, Orthopedics, Gastroenterology",
                "phone": "+91 422 2570170", "addr": "Peelamedu, Avinashi Rd, Coimbatore"
            },
            {
                "id": "hosp_1004",
                "name": "Ganga Hospital",
                "lat": 11.0195, "lon": 76.9512, "beds": 650,
                "em_spec": "24/7 Orthopedic Trauma & Plastic Surgery ICU",
                "best_sec": "Best Sector: Orthopedics & Reconstructive Microsurgery",
                "rating": 4.9, "reviews": 8420, "cat": "Super Specialty Hospital",
                "spec": "Orthopedics, Plastic Surgery, Trauma Care",
                "phone": "+91 422 2485000", "addr": "393, Mettupalayam Rd, Saibaba Colony, Coimbatore"
            },
            # North Coimbatore District - Mettupalayam & Karamadai
            {
                "id": "hosp_2001",
                "name": "Government Hospital, Mettupalayam",
                "lat": 11.2985, "lon": 76.9412, "beds": 250,
                "em_spec": "24/7 Emergency & Mountain Highway Trauma Care",
                "best_sec": "Best Sector: Highway Trauma & General Surgery",
                "rating": 4.4, "reviews": 1280, "cat": "Government District Hospital",
                "spec": "Emergency Medicine, General Surgery, Pediatrics",
                "phone": "+91 4254 222233", "addr": "Ooty Main Road, Mettupalayam, Coimbatore District"
            },
            {
                "id": "hosp_2002",
                "name": "Karamadai Rural Health Centre & Clinic",
                "lat": 11.2410, "lon": 76.9580, "beds": 80,
                "em_spec": "24/7 Primary Emergency & Maternity Care",
                "best_sec": "Best Sector: Primary Emergency & Pediatrics",
                "rating": 4.3, "reviews": 450, "cat": "Primary Healthcare Centre",
                "spec": "General Medicine, Maternity, Pediatrics",
                "phone": "+91 4254 273100", "addr": "Main Road, Karamadai, Coimbatore District"
            },
            # South Coimbatore District - Pollachi & Kinathukadavu
            {
                "id": "hosp_3001",
                "name": "Government Hospital, Pollachi",
                "lat": 10.6582, "lon": 77.0084, "beds": 350,
                "em_spec": "24/7 Emergency & Polytrauma Unit",
                "best_sec": "Best Sector: Maternal & Child Healthcare",
                "rating": 4.5, "reviews": 2340, "cat": "Government Taluk Hospital",
                "spec": "Obstetrics, Pediatrics, General Surgery, Orthopedics",
                "phone": "+91 4259 224411", "addr": "New Scheme Road, Pollachi, Coimbatore District"
            },
            {
                "id": "hosp_3002",
                "name": "Government Hospital, Kinathukadavu",
                "lat": 10.8272, "lon": 77.0205, "beds": 120,
                "em_spec": "24/7 Emergency & Maternity Services",
                "best_sec": "Best Sector: Emergency Triage & Maternity",
                "rating": 4.4, "reviews": 890, "cat": "Taluk Healthcare Centre",
                "spec": "Emergency Medicine, Pediatrics, General Medicine",
                "phone": "+91 4259 236222", "addr": "Pollachi Main Rd, Kinathukadavu, Coimbatore District"
            },
            {
                "id": "hosp_3003",
                "name": "Valparai Hill Emergency Clinic",
                "lat": 10.3260, "lon": 76.9540, "beds": 90,
                "em_spec": "24/7 Hill Station Emergency & Ambulance Station",
                "best_sec": "Best Sector: Emergency Stabilization & Snakebite ICU",
                "rating": 4.3, "reviews": 310, "cat": "Hill District Health Centre",
                "spec": "Emergency Medicine, Toxicology, Trauma Care",
                "phone": "+91 4253 222100", "addr": "Main Bazaar, Valparai, Coimbatore District"
            },
            # East & Northeast District - Sulur & Annur
            {
                "id": "hosp_4001",
                "name": "Sulur Air Force Station & Rural Hospital",
                "lat": 11.0280, "lon": 77.1250, "beds": 180,
                "em_spec": "24/7 Emergency & Trauma Care",
                "best_sec": "Best Sector: Aviation & Highway Emergency Care",
                "rating": 4.6, "reviews": 1120, "cat": "Community Hospital",
                "spec": "General Surgery, Orthopedics, Internal Medicine",
                "phone": "+91 422 2687200", "addr": "Trichy Road, Sulur, Coimbatore District"
            },
            {
                "id": "hosp_4002",
                "name": "Government Hospital, Annur",
                "lat": 11.2330, "lon": 77.1080, "beds": 140,
                "em_spec": "24/7 Emergency & Maternity ICU",
                "best_sec": "Best Sector: Primary Care & Maternity Services",
                "rating": 4.4, "reviews": 670, "cat": "Taluk Hospital",
                "spec": "General Medicine, Obstetrics, Pediatrics",
                "phone": "+91 4254 262300", "addr": "Sathy Road, Annur, Coimbatore District"
            }
        ]

        seed_records = []
        for idx, item in enumerate(district_hospitals):
            h_obj = HospitalDB(
                id=item["id"],
                name=item["name"],
                latitude=item["lat"],
                longitude=item["lon"],
                beds=item["beds"],
                emergency_specialty_24x7=item["em_spec"],
                best_sector=item["best_sec"],
                rating=item["rating"],
                review_count=item["reviews"],
                category=item["cat"],
                specialties=item["spec"],
                emergency_24x7=True,
                phone=item["phone"],
                address=item["addr"],
                review_snippet="Immediate 24/7 emergency response, modern facilities, and expert physicians."
            )
            seed_records.append(h_obj)

        db.add_all(seed_records)
        db.commit()
        print(f"[Database] Seeded {len(seed_records)} district-wide hospital spatial records into SQLite.")
    except Exception as e:
        db.rollback()
        print(f"[Database] Error seeding hospital records: {e}")
    finally:
        db.close()



def init_db():
    Base.metadata.create_all(bind=engine)
    seed_hospitals_if_empty()
    print(f"[Database] SQLite initialized with country_code & BIGINT 10-digit phone_number at: {DB_PATH}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()

