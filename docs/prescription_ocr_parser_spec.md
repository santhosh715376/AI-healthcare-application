# Prescription Parser Module Specification (`prescription_parser.py`)

## Executive Summary
This document specifies the exact architecture, data pipeline, normalization logic, and human-in-the-loop workflow for **Module 1: Prescription Parser (`agents/graphs/prescription_parser.py`)**. 

---

## 1. End-to-End Pipeline Architecture

```
                  +-----------------------------------+
                  |  INPUT SOURCE (Web Interface)     |
                  +-----------------------------------+
                                    │
            ┌───────────────────────┴───────────────────────┐
            │                                               │
  [Voice Mic Transcript]                           [Paper Slip Image Upload]
  (Web Speech / Whisper)                           (JPG / PNG / PDF File)
            │                                               │
            │                                               ▼
            │                                  +--------------------------+
            │                                  | EasyOCR Engine (Local)   |
            │                                  | lang=['en'], CPU Mode    |
            │                                  +--------------------------+
            │                                               │
            └───────────────────────┬───────────────────────┘
                                    │
                                    ▼
                     [Raw Unstructured Text Payload]
                                    │
                                    ▼
                     +-----------------------------+
                     | prescription_parser.py      |
                     | (LangGraph Structuring Node)|
                     +-----------------------------+
                                    │
                                    ▼
                     +-----------------------------+
                     | 3-Section Header-Body-Tail  |
                     | Structured JSON Output      |
                     +-----------------------------+
                                    │
                                    ▼
                     +-----------------------------+
                     | Live Notepad Review Modal   |
                     | (Human-in-the-Loop Confirmation)|
                     +-----------------------------+
                                    │
                                    ▼
                     +-----------------------------+
                     | Save to Patient Timeline DB |
                     | Tagged by Provenance Source |
                     +-----------------------------+
```

---

## 2. Component Specifications

### 2.1 OCR Ingestion Layer (EasyOCR)
- **Library:** `easyocr>=1.7.0`
- **Execution Mode:** CPU (`gpu=False`), English-only (`lang=['en']`).
- **Function:** Takes file bytes/image path, returns concatenated raw English text string.
- **Filtering Rule:** Ignore non-Latin Unicode characters and graphics noise.

### 2.2 LLM Structuring & Normalization Node
- **Framework:** LangChain / LangGraph with Pydantic structured output.
- **Shorthand Normalizer Dictionary:**
  - `TDS` / `tds` → `"Three times a day (1-1-1)"`
  - `BD` / `bd` → `"Twice a day (1-0-1)"`
  - `QD` / `qd` → `"Once a day (1-0-0)"`
  - `Q6H` / `q6h` → `"Every 6 hours"`
  - `PC` / `pc` → `"After Food"`
  - `AC` / `ac` → `"Before Food"`
  - `SOS` / `sos` → `"As needed"`
- **Strict Guardrail:** Extract explicitly recorded diagnoses ONLY (`recordedDiagnosis`). **NEVER infer or guess unstated diagnoses.**

### 2.3 Output JSON Contract (`contracts/schemas/prescription.schema.json`)
```json
{
  "id": "rx-pat-1001-01",
  "patientId": "pat-1001",
  "source": "patient_ocr",
  "header": {
    "doctorName": "Dr. Nithin Narayanan",
    "hospitalName": "CHC Nemmara",
    "opdContact": "+91 8086993168",
    "date": "20-09-2022"
  },
  "body": {
    "recordedDiagnosis": "URTI (Upper Respiratory Tract Infection)",
    "medications": [
      {
        "name": "Syp Calpol (250/5)",
        "dosage": "4ml",
        "frequency": "Every 6 hours (Q6H)",
        "duration": "3 days",
        "foodRelation": "After Food"
      },
      {
        "name": "Syp Delcon",
        "dosage": "3ml",
        "frequency": "Three times a day (TDS)",
        "duration": "5 days",
        "foodRelation": "After Food"
      }
    ]
  },
  "tail": {
    "advice": "Rest and hydrate well.",
    "followUpDate": "In 5 days"
  }
}
```

---

## 3. Human-in-the-Loop Confirmation Workflow

1. **Upload / Speak:** User uploads paper slip photo or speaks prescription transcript.
2. **FastAPI Processing:** Endpoint `POST /api/prescriptions/parse` runs `prescription_parser.py` and returns structured JSON in < 2 seconds.
3. **Notepad Preview:** Frontend opens a 3-section live editable notepad modal.
4. **User Confirm:** User makes any 3-second quick fixes and taps **"Confirm & Save"**.
5. **DB Commit:** Backend stores record with `source: "doctor_voice"`, `source: "doctor_ocr"`, or `source: "patient_ocr"`.

---

## 4. Evaluation Checklist Before Writing Code

- [ ] Does the 3-section Header-Body-Tail schema match your expectation for doctor prescriptions?
- [ ] Are you aligned on using EasyOCR locally for image text extraction?
- [ ] Are you ready to authorize implementing `agents/graphs/prescription_parser.py` based on this spec?
