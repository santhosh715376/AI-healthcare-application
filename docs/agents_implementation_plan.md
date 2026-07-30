# Agents & Chatbot Implementation Plan

## Executive Summary
This document specifies the architecture, data schemas, guardrails, and implementation plan for the **Agents & Chatbot Module (`agents/`)**. Implementation will strictly follow this document upon user approval.

---

## 1. Module Overview & Architecture

The `agents/` folder exposes AI endpoints via FastAPI (`server.py`) serving 4 core LangGraph/Python modules:

```
agents/
├── state.py                      # Shared LangGraph State definitions
├── graphs/
│   ├── prescription_parser.py    # Module 1: EasyOCR + Header-Body-Tail Parser
│   ├── specialty_suggestion.py   # Module 2: Symptom → Specialty Tag Categorizer
│   ├── hospital_ranking.py       # Module 3: Fact-Based Proximity & Insurance Ranker
│   └── drug_info_rag.py          # Module 4: Consent-Gated Timeline & openFDA Chatbot
├── server.py                     # FastAPI Endpoint Router
└── requirements.txt
```

---

## 2. Component Specifications

### Module 1: Prescription Parser (`prescription_parser.py`)
- **Input:** Spoken transcript text or Image file upload (JPG/PNG).
- **OCR Engine:** `EasyOCR` (Python open-source, local CPU engine, $0 cost).
- **Structuring Engine:** LLM node enforcing `contracts/schemas/prescription.schema.json`.
- **Output Schema (3-Section Header-Body-Tail):**
  - **Header:** `doctorName`, `hospitalName`, `opdContact`, `date`.
  - **Body:** `recordedDiagnosis` (Explicitly stated only), `medications` array (`name`, `dosage`, `frequency`, `duration`, `foodRelation`).
  - **Tail:** `advice`, `followUpDate`.
- **Guardrails:**
  - **Strict Non-Inference:** Extract recorded diagnoses ONLY. Never infer or generate new diagnoses.
  - **Shorthand Normalization:** Convert `TDS` → `Three times daily (1-1-1)`, `PC` → `After Food`, `AC` → `Before Food`.
  - **Provenance Tagging:** Output `source: "doctor_voice"`, `source: "doctor_ocr"`, or `source: "patient_ocr"`.

### Module 2: Specialty Suggestion Agent (`specialty_suggestion.py`)
- **Input:** Free-text symptom string (e.g., `"chest pain"`).
- **Output:** Tappable specialty tag chips (e.g., `["Cardiology", "Pulmonology"]`) + mandatory disclaimer.
- **Guardrails:** Output is a search filter, not a diagnosis.

### Module 3: Hospital Ranking Agent (`hospital_ranking.py`)
- **Input:** Filtered hospital list + priority weights (`{ distance: 0.4, insurance: 0.3, emergency: 0.3 }`).
- **Output:** Sorted shortlist + 1-line reason per hospital.
- **Guardrails:** Rank strictly on verifiable facts (`distance`, `bedCount`, `acceptedInsurance`, `emergencyServices`). No invented ratings.

### Module 4: Drug-Info & Timeline Chatbot (`drug_info_rag.py`)
- **Input:** Patient query + Consent-filtered Timeline Context.
- **Data Source:** openFDA / RxNorm APIs + Patient Timeline Record.
- **Guardrails:**
  - Refuse medical advice/dosage changes.
  - Respect consent scope (`FULL` vs `MEDS_ONLY`). If `MEDS_ONLY`, strip diagnosis from LLM context window.

---

## 3. Data Contract Alignment

All outputs strictly validate against JSON schemas defined in `contracts/schemas/`:
- `prescription.schema.json`
- `agent-response.schema.json`
- `patient.schema.json`
- `hospital.schema.json`

---

## 4. Execution Steps for User Review

1. **Step 1:** Review and approve this implementation specification document.
2. **Step 2:** Implement `agents/state.py` Pydantic state models.
3. **Step 3:** Implement `agents/graphs/prescription_parser.py` (EasyOCR + 3-Section Parser).
4. **Step 4:** Implement `agents/graphs/specialty_suggestion.py` & `hospital_ranking.py`.
5. **Step 5:** Implement `agents/graphs/drug_info_rag.py`.
6. **Step 6:** Bind all graphs to FastAPI routes in `agents/server.py` and test against `contracts/mock-data/`.
