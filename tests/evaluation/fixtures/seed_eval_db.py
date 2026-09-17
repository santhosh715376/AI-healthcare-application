import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure agents is on sys.path
agents_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "agents"))
if agents_path not in sys.path:
    sys.path.insert(0, agents_path)

import database
from database import Base, DoctorDB, PatientDB, PrescriptionDB, HospitalDB, AdherenceScheduleDB, AdherenceLogDB

EVAL_PATIENTS = [
    {
        "id": 100001,
        "name": "Arjun Sharma",
        "email": "arjun.sharma@eval.test",
        "country_code": "+91",
        "phone_number": 9876543210,
        "password_hash": "$2b$12$eXampleHashPlaceholder1234567890",
        "age": 34,
        "gender": "Male",
        "blood_group": "O+"
    },
    {
        "id": 100002,
        "name": "Priya Nair",
        "email": "priya.nair@eval.test",
        "country_code": "+91",
        "phone_number": 9876543211,
        "password_hash": "$2b$12$eXampleHashPlaceholder1234567890",
        "age": 29,
        "gender": "Female",
        "blood_group": "B+"
    }
]

EVAL_DOCTORS = [
    {
        "id": 500001,
        "name": "Dr. Ramesh Kumar",
        "email": "dr.ramesh@eval.test",
        "country_code": "+91",
        "phone_number": 9123456780,
        "password_hash": "$2b$12$eXampleHashPlaceholder1234567890",
        "doc_license": "NMC-TN-50001",
        "hospital_name": "PSG Hospitals",
        "specialty": "General Medicine"
    },
    {
        "id": 500002,
        "name": "Dr. Kavitha Menon",
        "email": "dr.kavitha@eval.test",
        "country_code": "+91",
        "phone_number": 9123456781,
        "password_hash": "$2b$12$eXampleHashPlaceholder1234567890",
        "doc_license": "NMC-TN-50002",
        "hospital_name": "KMCH",
        "specialty": "Endocrinology"
    }
]

EVAL_PRESCRIPTIONS = [
    {
        "id": "rx-eval-001",
        "patient_id": 100001,
        "doctor_id": 500001,
        "source": "doctor_voice",
        "patient_name": "Arjun Sharma",
        "patient_country_code": "+91",
        "patient_phone_number": 9876543210,
        "doctor_name": "Dr. Ramesh Kumar",
        "hospital_name": "PSG Hospitals",
        "recorded_diagnosis": "Acute Viral Upper Respiratory Tract Infection (URTI)",
        "medications_json": [
            {"name": "Paracetamol", "dosage": "500mg", "frequency": "1-1-1", "duration": "5 days", "foodRelation": "After Food"},
            {"name": "Cetrizine", "dosage": "10mg", "frequency": "0-0-1", "duration": "5 days", "foodRelation": "After Food"}
        ],
        "dietary_advice_json": {"diet": "Warm fluids, light diet, avoid cold items"},
        "advice": "Rest well, drink plenty of warm water, monitor temperature daily.",
        "follow_up_date": "2026-09-25",
        "visit_summary": "Patient presented with fever and sore throat. Diagnosed with acute URTI. Started on Paracetamol and Cetrizine."
    },
    {
        "id": "rx-eval-002",
        "patient_id": 100002,
        "doctor_id": 500002,
        "source": "doctor_voice",
        "patient_name": "Priya Nair",
        "patient_country_code": "+91",
        "patient_phone_number": 9876543211,
        "doctor_name": "Dr. Kavitha Menon",
        "hospital_name": "KMCH",
        "recorded_diagnosis": "Type 2 Diabetes Mellitus — Uncontrolled",
        "medications_json": [
            {"name": "Metformin", "dosage": "500mg", "frequency": "1-0-1", "duration": "30 days", "foodRelation": "After Food"},
            {"name": "Glipizide", "dosage": "5mg", "frequency": "1-0-0", "duration": "30 days", "foodRelation": "Before Food"}
        ],
        "dietary_advice_json": {"diet": "Low glycemic index, strictly avoid refined sugars and high carbohydrate foods"},
        "advice": "Monitor fasting and post-prandial blood sugar levels weekly. Walk 30 minutes daily.",
        "follow_up_date": "2026-10-20",
        "visit_summary": "Follow-up for poorly controlled blood sugar. Prescribed Metformin and Glipizide with strict dietary counseling."
    }
]

EVAL_HOSPITALS = [
    {
        "id": "hosp_eval_1",
        "name": "Kovai Medical Center and Hospital (KMCH)",
        "latitude": 11.0424,
        "longitude": 77.0378,
        "beds": 750,
        "category": "Super Specialty Hospital",
        "specialties": "Cardiology, Trauma, Emergency Medicine",
        "emergency_specialty_24x7": "24/7 Level-1 Trauma & Emergency ICU",
        "facilities_json": ["24/7 Level-1 Trauma", "Cardiac Cath Lab", "Pediatric ICU"],
        "best_sector": "Emergency & Cardiac Care",
        "rating": 4.8,
        "review_count": 4250,
        "emergency_24x7": True,
        "phone": "+91 422 4323800",
        "address": "Avinashi Road, Coimbatore"
    },
    {
        "id": "hosp_eval_2",
        "name": "Sri Ramakrishna Hospital",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "beds": 600,
        "category": "Multispecialty Hospital",
        "specialties": "Cardiology, Pediatrics, Emergency Care",
        "emergency_specialty_24x7": "24/7 Emergency & Pediatric ICU",
        "facilities_json": ["24/7 Emergency", "Pediatric ICU"],
        "best_sector": "Pediatric & Multi-Specialty Care",
        "rating": 4.7,
        "review_count": 3100,
        "emergency_24x7": True,
        "phone": "+91 422 4500000",
        "address": "Siddhapudur, Coimbatore"
    }
]

def create_in_memory_eval_db():
    """
    Creates and seeds an isolated in-memory SQLite database for deterministic evaluations.
    Guarantees zero mutation or pollution to the live database.
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for p in EVAL_PATIENTS:
        session.add(PatientDB(**p))
    for d in EVAL_DOCTORS:
        session.add(DoctorDB(**d))
    for rx in EVAL_PRESCRIPTIONS:
        session.add(PrescriptionDB(**rx))
    for h in EVAL_HOSPITALS:
        session.add(HospitalDB(**h))

    session.commit()
    return engine, Session
