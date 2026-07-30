# Comprehensive System Architecture (HLD & LLD): Database, AI & Component Workflows

## 1. High-Level Design (HLD)

The **Personalized Healthcare System** is a dual-portal clinical platform designed to provide strict component isolation between **Physicians (Doctor OPD Workspace)** and **Healthcare Consumers (Patient Portal)**.

### System Architecture Diagram

```text
 ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   REACT FRONTEND (Vite / React 18)                             │
 ├────────────────────────────────────────────────┬────────────────────────────────────────────────┤
 │               👨‍⚕️ DOCTOR PORTAL                │                👤 PATIENT PORTAL               │
 │ • NMC License Authentication                   │ • Patient Signup / Login (Mobile & Email)      │
 │ • Exact Search Indexing (Phone / Name / ID)    │ • Gemini 2.0 Flash Vision Paper Slip OCR       │
 │ • Voice Push-To-Talk STT (Groq Whisper)        │ • Comprehensive Cross-Doctor Timeline          │
 │ • Doctor Clinical Research RAG Chatbot         │ • Consumer Health AI Chatbot (Guardrailed)     │
 └───────────────────────┬────────────────────────┴────────────────────────┬───────────────────────┘
                         │                                                 │
                         │             REST API / JSON (HTTP)              │
                         ▼                                                 ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                  FASTAPI AI AGENT BACKEND SERVER                                │
 ├─────────────────────────────────────────────────────────────────────────────────────────────────┤
 │  [Auth & Security Module]     [AI Orchestration Engine]        [Database Engine]                 │
 │  • Bcrypt Password Hashing    • Groq Llama 3.1 8B Instant      • SQLAlchemy ORM                  │
 │  • PyJWT Token Manager        • Groq Llama 3.3 70B RAG         • SQLite (`healthcare.db`)        │
 │  • BIGINT Phone Validation    • Gemini 2.0 Flash Multimodal    • Dual Table & Ledger Schemas     │
 └───────────────────────┬────────────────────────┬────────────────────────┬───────────────────────┘
                         │                        │                        │
                         ▼                        ▼                        ▼
 ┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌───────────────────────────────┐
 │        Groq LPU Cloud         │ │       Google Gemini Cloud     │ │    SQLite Local Storage       │
 │ • Whisper-large-v3 STT        │ │ • Gemini 2.0 Flash Vision     │ │ • `doctors` Table             │
 │ • Llama-3.1-8b-instant        │ │   (Handwritten OCR)           │ │ • `patients` Table            │
 │ • Llama-3.3-70b-versatile     │ │                               │ │ • `prescriptions` Ledger      │
 └───────────────────────────────┘ └───────────────────────────────┘ └───────────────────────────────┘
```

---

## 2. Low-Level Design (LLD) & Relational Database Schemas

### A. Dual-Table User Isolation & Professional Phone Architecture

To support international country codes (`+91`, `+1`) while strictly enforcing 10-digit integer phone validation, phone storage is decoupled into `country_code` (`TEXT`) and `phone_number` (`BIGINT`).

#### 1. `doctors` Table Schema
```sql
CREATE TABLE doctors (
    sno INTEGER PRIMARY KEY AUTOINCREMENT,
    id INTEGER UNIQUE NOT NULL,                  -- 6-digit random integer (e.g. 849201)
    name TEXT NOT NULL,                          -- Full Doctor Name (e.g. Dr. Nithin Narayanan)
    email TEXT UNIQUE NOT NULL,                  -- Validated RFC-5322 email
    country_code TEXT NOT NULL DEFAULT '+91',    -- Country code e.g. '+91', '+1'
    phone_number BIGINT NOT NULL,                -- Exact 10-digit integer
    password_hash TEXT NOT NULL,                 -- Bcrypt hashed password string
    doc_license TEXT UNIQUE NOT NULL,            -- NMC License ID (e.g. NMC-TN-88492)
    hospital_name TEXT NOT NULL,                 -- Primary Hospital/Clinic affiliation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doctor_phone UNIQUE (country_code, phone_number),
    CONSTRAINT check_doctor_phone_10digits CHECK (phone_number BETWEEN 1000000000 AND 9999999999)
);
CREATE INDEX idx_doctors_license ON doctors(doc_license);
CREATE INDEX idx_doctors_phone ON doctors(phone_number);
```

#### 2. `patients` Table Schema
```sql
CREATE TABLE patients (
    sno INTEGER PRIMARY KEY AUTOINCREMENT,
    id INTEGER UNIQUE NOT NULL,                  -- 6-digit random integer (e.g. 100001)
    name TEXT NOT NULL,                          -- Full Patient Name (e.g. Santhosh Kumar)
    email TEXT UNIQUE NOT NULL,                  -- Validated RFC-5322 email
    country_code TEXT NOT NULL DEFAULT '+91',    -- Country code e.g. '+91', '+1'
    phone_number BIGINT NOT NULL,                -- Exact 10-digit integer
    password_hash TEXT NOT NULL,                 -- Bcrypt hashed password string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_patient_phone UNIQUE (country_code, phone_number),
    CONSTRAINT check_patient_phone_10digits CHECK (phone_number BETWEEN 1000000000 AND 9999999999)
);
CREATE INDEX idx_patients_phone ON patients(phone_number);
```

---

### B. Central Prescriptions Ledger Schema (`prescriptions`)

The `prescriptions` table operates as a central **Many-to-Many consultation ledger**.

```sql
CREATE TABLE prescriptions (
    id TEXT PRIMARY KEY,                         -- e.g. rx-100001-20260730095713
    patient_id INTEGER NOT NULL,                 -- Foreign Key -> patients.id
    doctor_id INTEGER,                           -- Foreign Key -> doctors.id
    source TEXT NOT NULL,                        -- 'doctor_voice' | 'doctor_ocr' | 'patient_ocr'
    patient_name TEXT NOT NULL,                  -- Cached for Doctor OPD search & display
    patient_country_code TEXT NOT NULL DEFAULT '+91',
    patient_phone_number BIGINT NOT NULL,        -- Exact 10-digit integer
    doctor_name TEXT NOT NULL,                   -- Cached for Patient Prescription view
    hospital_name TEXT NOT NULL,                 -- Cached for Patient Prescription view
    recorded_diagnosis TEXT,                    -- Explicitly stated diagnosis ONLY
    medications_json TEXT NOT NULL,              -- JSON array of drugs with routine timing & duration
    dietary_advice_json TEXT,                    -- JSON object of recommended foods, items to avoid & remedies
    advice TEXT,                                 -- General dietary/lifestyle instructions
    follow_up_date TEXT,                         -- Clinical text string e.g. "In 5 days / SOS"
    visit_summary TEXT,                          -- Narrative visit summary generated by Groq
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id),
    FOREIGN KEY(doctor_id) REFERENCES doctors(id)
);
CREATE INDEX idx_prescriptions_patient_id ON prescriptions(patient_id);
CREATE INDEX idx_prescriptions_doctor_id ON prescriptions(doctor_id);
CREATE INDEX idx_prescriptions_patient_phone ON prescriptions(patient_phone_number);
```

---

## 3. Extended Schema Payload Structures

### A. Medications Routine & Duration Schema (`medications_json`)
Doctors specify routine timing (Morning, Noon, Night) and duration in days for each drug.

```json
[
  {
    "name": "Syp Calpol 250/5",
    "dosage": "5ml",
    "frequency": "1-1-1",
    "routine": { "morning": true, "noon": true, "night": true },
    "duration": "5 days",
    "foodRelation": "After Food"
  }
]
```

### B. Dietary, Lifestyle & Traditional Remedies Schema (`dietary_advice_json`)
Indian clinical consultations frequently include non-pharmacological care guidelines:

```json
{
  "recommendedFoods": [
    "Citrus fruits (Orange, Amla)",
    "Warm vegetable soups",
    "Hydration (3 Liters water/day)"
  ],
  "foodsToAvoid": [
    "Cold ice cream & refrigerated drinks",
    "Oily fried snacks",
    "Excessive caffeine"
  ],
  "traditionalRemedies": [
    "Turmeric warm milk at bedtime",
    "Eucalyptus steam inhalation 2x/day",
    "Warm salt water gargle"
  ]
}
```

---

## 4. OPD Search Indexing & Scoping Rules

### A. Doctor OPD Search Scoping (Exact Input Match)
- **Input:** 10-Digit Phone Number (`9876543210`), Patient Name (`Santhosh`), or Patient ID (`100001`).
- **SQL Logic:**
  ```sql
  SELECT p.* FROM prescriptions p
  JOIN patients pat ON p.patient_id = pat.id
  WHERE (pat.phone_number = :parsed_10digit_int OR LOWER(pat.name) = LOWER(:query) OR CAST(pat.id AS TEXT) = :query)
    AND p.doctor_id = :current_doctor_id
  ORDER BY p.created_at DESC;
  ```
- **Privacy Enforcement:** A Doctor sees **ONLY consultations THAT SPECIFIC DOCTOR HAS PERFORMED** with the patient.

---

## 5. Rationale: Why These Design Decisions Were Made

1. **Why `country_code` (TEXT) and `phone_number` (BIGINT) were split:**
   - Enforces an exact 10-digit integer constraint (`CHECK (phone_number BETWEEN 1000000000 AND 9999999999)`) while seamlessly supporting international country codes (`+91`, `+1`).
   - A composite unique constraint `UNIQUE(country_code, phone_number)` guarantees phone number uniqueness per country.
2. **Why `follow_up_date` is `TEXT` instead of `DATETIME`:**
   - Doctors speak/write follow-ups as clinical recommendations (*"In 5 days"*, *"SOS if fever returns"*). Forcing strict `DATETIME` causes database insertion exceptions.
3. **Why System Automatic Timestamping is Enforced:**
   - Doctors never type or speak dates. The database stamps `created_at` automatically on `POST /api/timeline/save`.
