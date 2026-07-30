# Implementation Plan: Doctor & Patient Authentication & JWT Flow

## 1. Problem Statement
[Certain] You have not updated the Doctor & Patient authentication backend endpoints. 
While `agents/auth.py` contains password hashing and phone validation helper functions, **`agents/server.py` is missing the FastAPI authentication routes**:
- Missing `POST /api/auth/register/doctor`
- Missing `POST /api/auth/register/patient`
- Missing `POST /api/auth/login/doctor`
- Missing `POST /api/auth/login/patient`

When a user fills out the registration form in the UI screenshot, the frontend cannot submit to a working authentication API endpoint.

## 2. Why is it a Problem?
- **Registration Failure:** Submitting the registration form in the Doctor or Patient portal fails or falls back to mock memory.
- **Missing Doctor Specialty:** The doctor registration form needs to accept and store `specialty` (e.g. `General Medicine`, `Cardiology`) alongside `hospital_name` and `doc_license`.
- **Phone Validation:** Phone inputs must strictly validate exact 10-digit integers (`BIGINT`) with country code parsing (`+91`), rejecting invalid strings before hitting SQLite.

## 3. Solution Expected

Implement the full production-grade Auth layer in `agents/server.py`:

1. **`POST /api/auth/register/doctor`:**
   - Payload: `name`, `email`, `phone` (10-digit), `doc_license`, `hospital_name`, `specialty` (default "General Medicine"), `password`.
   - Process: Validates email format + 10-digit phone, hashes password with `bcrypt`, generates random 6-digit doctor `id`, inserts into `doctors` table, issues JWT token (`role = "DOCTOR"`).

2. **`POST /api/auth/register/patient`:**
   - Payload: `name`, `email`, `phone` (10-digit), `password`.
   - Process: Validates email + 10-digit phone, hashes password with `bcrypt`, generates random 6-digit patient `id`, inserts into `patients` table, issues JWT token (`role = "PATIENT"`).

3. **`POST /api/auth/login/doctor` & `POST /api/auth/login/patient`:**
   - Accepts 10-digit phone or email + password, verifies bcrypt hash, returns JWT bearer token + user metadata.

4. **Frontend Integration:** Wire React signup/login modal forms to `http://localhost:8000/api/auth/...`.

---

## 4. Possible Solutions Comparison

| Option | Approach | Pros | Cons | Decision |
|---|---|---|---|---|
| **Option A (Mock Local Storage)** | Keep authentication purely in React state without backend persistence | Fast mock testing | User accounts disappear on page refresh; doctor NMC licenses not verified against DB | **Rejected** |
| **Option B (Bcrypt + JWT + SQLite Dual-Table Persistence - Recommended)** | Implement FastAPI auth endpoints in `agents/server.py` backed by `DoctorDB` and `PatientDB` with JWT security | Production-grade security; persists NMC licenses, hospital names, specialties, and 10-digit phone validation | Requires writing FastAPI routes | **Chosen** |

**Why Option B instead of Option A:**
[Certain] Option B satisfies your LLD security architecture specification (`docs/system_architecture_hld_lld.md`) and guarantees that doctor licenses and hospital affiliations are stored in SQLite.

---

## 5. Architecture & Data Flow

```text
 ┌──────────────────────────────────────────────────────────────────────────────────────────┐
 │                               DOCTOR & PATIENT AUTHENTICATION                            │
 ├──────────────────────────────────────────────────────────────────────────────────────────┤
 │                                                                                          │
 │  ┌─────────────────────────────────┐           ┌─────────────────────────────────┐       │
 │  │      👨‍⚕️ Doctor Signup Form       │           │      👤 Patient Signup Form      │       │
 │  │ (Name, Email, 10-Digit Phone,   │           │ (Name, Email, 10-Digit Phone,   │       │
 │  │  NMC License, Hospital, Spec)  │           │  Password)                      │       │
 │  └────────────────┬────────────────┘           └────────────────┬────────────────┘       │
 │                   │                                             │                        │
 │                   ▼                                             ▼                        │
 │  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
 │  │                     FASTAPI AUTH ROUTER (`agents/server.py`)                       │  │
 │  ├────────────────────────────────────────────────────────────────────────────────────┤  │
 │  │ • `parse_phone_number()` → Validates exact 10-digit integer                        │  │
 │  │ • `hash_password()` → Bcrypt salt + hash                                           │  │
 │  │ • `generate_6digit_id()` → 6-digit integer PK                                      │  │
 │  │ • `create_access_token()` → JWT bearer token generation                            │  │
 │  └────────────────┬─────────────────────────────────────────────┬─────────────────────┘  │
 │                   │                                             │                        │
 │                   ▼                                             ▼                        │
 │  ┌─────────────────────────────────┐           ┌─────────────────────────────────┐       │
 │  │   `DoctorDB` (SQLite WAL Engine)│           │  `PatientDB` (SQLite WAL Engine)│       │
 │  └─────────────────────────────────┘           └─────────────────────────────────┘       │
 └──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Verification Plan

### Automated Verification
1. `python scratch/test_auth_endpoints.py`: Run automated test script executing Doctor Registration, Patient Registration, Doctor Login, and Patient Login against `http://localhost:8000` to verify 200 OK responses and valid JWT tokens.

---

Review this Implementation Plan artifact and click **Proceed** (or reply to confirm) so I can implement the Auth endpoints in `agents/server.py`.
