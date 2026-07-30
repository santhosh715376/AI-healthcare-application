# Implementation Plan: Greeting Handler & Patient Timeline Context Lookup

## Executive Summary & Problem Diagnosis

### The Issue:
When a patient types a non-specific greeting like `"hi"`, `"hello"`, or `"hey"`, the AI chatbot was previously falling through to the **Differential Likelihood Ranking Agent**, which erroneously returned a 40% probability for *Anxiety* and recommended *Psychiatry*.

### The Correct Behavior:
1. **Greeting Detection:** When the patient sends a greeting (`hi`, `hello`, `hey`, `good morning`), the system intercepts it with a **Greeting Agent** rather than a symptom triage agent.
2. **Database Timeline Lookup:** The Greeting Agent queries SQLite (`healthcare.db` -> `prescriptions`) using the patient's phone number to fetch their **most recent visit record**, including:
   - **Visit Date** (e.g., *July 25, 2026*)
   - **Doctor Name** (e.g., *Dr. Nithin*)
   - **Recorded Diagnosis** (e.g., *Type 2 Diabetes & Acute Gastritis*)
   - **Prescribed Medications** (e.g., *Metformin 500mg, Omeprazole 20mg*)
3. **Personalized Contextual Greeting:** The agent responds with a warm, empathetic greeting checking in on their specific condition:
   > *"Hello Santhosh! How can I help you today?*\n\n*I reviewed your recent medical record from **July 25, 2026** with **Dr. Nithin** regarding **Type 2 Diabetes & Acute Gastritis** (Prescribed: Metformin 500mg, Omeprazole 20mg).*\n\n*How is your well-being and recovery with this condition today?*\n\n*Feel free to ask any health question, describe new symptoms, or use shortcuts like `/specialty`, `/comfort`, `/triage`, or `/emergency`."*
4. **Strict Guardrail Boundary:** If the user asks about any condition or drug **outside** their recorded database history, the Timeline Guardrail triggers:
   > *"Please consult your prescribing doctor for medicines and share your health concerns with them."*

---

## 🛠️ Proposed Component Updates

### 1. Backend Agent (`agents/graphs/patient_advisor_agent.py`)
- Implement `get_recent_patient_timeline_summary(patient_phone)` function querying `PrescriptionDB` by `patient_phone_number`.
- Add Greeting interceptor (`greetings = ["hi", "hello", "hey", ...]`) at index 0 of `process_patient_advisor_pipeline`.

### 2. FastAPI Endpoint (`agents/server.py`)
- Ensure `POST /api/chat/patient-advisor` passes `patientPhone` to `process_patient_advisor_pipeline`.

### 3. Frontend Chat Bubble (`frontend/src/pages/ChatPage.jsx`)
- Render formatted greeting response with bold condition badges and action suggestions.

---

## 🧪 Verification Plan

### Automated Verification:
- Run `python scratch/verify_patient_advisor_agent.py` testing:
  1. Input `"hi"` with patient phone `918438228303` ➔ Returns Greeting Agent response with Dr. Nithin's recent prescription timeline record.
  2. Input `"Can I take Amoxicillin?"` ➔ Returns Timeline Guardrail block.

---

## 🛑 User Review Required

Please review this implementation plan. **No code or server commands will be executed until you reply with "proceed".**
