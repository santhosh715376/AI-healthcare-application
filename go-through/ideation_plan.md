# Healthcare MVP Ideation & Architecture Plan (`ideation_plan.md`)

This document captures the complete technical vision, feature breakdown, and hybrid AI architecture for the Healthcare MVP.

---

## 1. System Vision & Core Principles

- **Primary Goal:** Eliminate EHR click-fatigue for doctors and bridge the last-mile digital health record gap for patients in India.
- **Strict Clinical Guardrail:** **No AI-asserted diagnoses, ever.** The system relays documented clinician judgments (`recordedDiagnosis`) and facts only.
- **Execution Rule:** "AI where it earns its place, and nowhere else." Decision support over verified data.

---

## 2. Hybrid AI Model Strategy

| Service / Feature | AI Model / Engine | Latency / Output |
| :--- | :--- | :--- |
| **Voice-to-Text (STT - Live)** | Web Speech API (Browser Native) | **0ms** real-time text streaming on UI |
| **Voice-to-Text (STT - Audio Upload)** | Groq Hosted Whisper (`whisper-large-v3`) | **< 200ms** high-accuracy transcription |
| **Prescription Structuring** | Groq LLM (`llama-3.3-70b-versatile`) | **< 300ms** 3-Section Header-Body-Tail JSON |
| **Handwritten Prescription OCR** | Gemini 2.0 Flash (`gemini-2.0-flash` Vision) | **< 1.5s** 1-step image-to-JSON extraction |
| **Specialty Categorizer** | Groq LLM (`llama-3.3-70b-versatile`) | **< 150ms** symptom text -> hospital specialty tags |
| **Patient Drug-Info Chatbot** | Groq LLM + OpenFDA RAG Retriever | **< 400ms** verified drug factual answers |

---

## 3. Module & Workflow Specs

### Module 1: Split-Pane Prescription Capture (`/doctor/capture`)
- **Left Pane:** Live updating voice transcript (Web Speech API / Groq Whisper).
- **Right Pane:** Real-time rendered 3-Section Header-Body-Tail card (`prescription.schema.json`).
- **OCR Tab:** Upload area for handwritten paper slips -> Gemini 2.0 Flash Vision -> Structured preview modal -> Save to DB.

### Module 2: Custom Patient Schedule & Calendar Sync
- **Doctor Input:** Relative frequencies (`1-0-1`, `TDS`, `Before/After Food`). No hard clock times.
- **Patient Mapping:** Custom routine slots (`Morning = 8:30 AM`, `Noon = 1:30 PM`, `Night = 9:30 PM`).
- **Native Device Sync:** 1-click **Add to Google Calendar / Apple iCal** sync. Native phone push notifications without keeping web app open.

### Module 3: Proof-of-Adherence Verification
When an alarm triggers, the patient satisfies check-in using 1 of 3 functions:
1. **Quick Pill Tap:** One-click timestamped button ("Taken at 8:32 AM").
2. **Photo Proof:** 1-second photo of pill/blister strip.
3. **Voice Check-in:** Speak "Took my morning dose".

### Module 4: Twilio WhatsApp Escalation Engine
- If verification is **NOT** completed within 30 minutes of scheduled time:
  - Dose status flips from `Pending` -> `MISSED`.
  - Backend fires a **Twilio WhatsApp API** message to the registered alternate caretaker / family contact:
    > *"⚠️ Emergency Alert: [Patient Name] missed their 8:30 AM Paracetamol dose. Please check on them."*

### Module 5: Emergency Hospital Discovery Map (`/map`)
- **Location:** Coimbatore District dataset (`coimbatore_hospitals.json`).
- **Specialty Categorizer:** Symptom search box (e.g. *"chest pain"*) -> Groq maps to `Cardiology` tag -> filters map markers.
- **Ranking Agent:** Groq ranks hospitals by verified facts (Distance, 24/7 status, Insurance match, Beds).

---

## 4. Development Execution Order

1. **Phase 1: Backend Agents (`agents/server.py` & `ocr_engine/main.py`)**
   - Groq & Gemini endpoints.
2. **Phase 2: Prescription Capture UI (`CapturePage.jsx`)**
   - Split-pane Voice + OCR workspace.
3. **Phase 3: Patient Timeline & Calendar Sync (`TimelinePage.jsx`)**
   - Routine mapping, iCal sync, and Adherence modal.
4. **Phase 4: Emergency Map & Twilio Integration (`MapPage.jsx`)**
   - Specialty categorization & WhatsApp escalation trigger.
