# Website — Basic Structure (for the frontend teammate)

Not a visual design spec — that's your call. This is the page inventory, what each page needs to *do*, and the flow between them, so the look can be built without guessing at missing functionality.

## Site map

```
/                        → Landing / role select (Patient / Doctor)
/login                    → Phone number lookup (mocked OTP for demo)
/patient
  /timeline               → Patient-facing view (component #8)
  /profile                → Self + dependent profiles (components #4, #5)
  /consent/:appointmentId  → Consent picker: full / meds-only / nothing (#9)
  /emergency               → Manual emergency trigger button (#11)
  /hospitals               → Hospital discovery — map + specialty browse + agents (#13)
  /medicines (stretch)     → OTC ordering + reorder-gated Rx meds (#14–15)
/doctor
  /capture                 → Voice/tap prescription capture (#1) + OCR fallback (#2)
  /summary/:patientId       → Doctor-facing summary card (#7) — respects consent scope
```

## Page-by-page functional requirements

### 1. Landing / role select
- Two entry points: "I'm a patient" / "I'm a doctor." No login wall before this — friction kills demo flow.

### 2. Login (mocked OTP)
- Phone number in → fake OTP → resolves to internal patient ID, not phone-as-identity. Surfacing this distinction ("phone is just how we found you") is a good demo beat, not just backend plumbing.

### 3. Patient timeline
- Chronological list: date, doctor, meds prescribed, diagnosis-as-recorded. Plain language, no medical jargon requiring explanation.
- Source badge per entry: "voice" vs "OCR" (traceability, matches component #6).

### 4. Profile + dependents
- One phone number → multiple patient cards (self, child, elderly parent).
- Accessibility fields as structured *and* free text — don't force a dropdown-only UI here, some conditions need a sentence.
- If a dependent profile includes disability data: show a guardian-consent step (DPDP Rules 2025 flag from the doc) — this can be a simple checkbox/modal for the demo, but it needs to visibly exist.

### 5. Consent picker (per appointment)
- Three clear options, radio-style, not a settings-page buried toggle: **Full history / Current meds only / Nothing**.
- One line of copy explaining that "meds only" hides the diagnosis field too — this is a real design decision from the doc (§9), make it visible, not implicit.

### 6. Emergency trigger
- One big, unambiguous button. Not buried in a menu — component #11 depends on this being fast to find under stress.
- On trigger: shows what's happening ("Notifying [contact name]... Surfacing nearby hospitals...") — don't let it feel like a silent black box.

### 7. Hospital discovery (component #13 — your two agents live here)
- Default view: map, nearest-first, live location (13a).
- Toggle: "Browse by specialty" → tag chips (Cardiology, Orthopedics, etc.) (13b).
- Free-text box: "What's going on?" → specialty-suggestion agent returns tappable specialty chips + disclaimer line ("suggested based on keywords, not a diagnosis") (13c).
- Once filtered: ranked shortlist, one-line reason per hospital, with a visible weighting control ("Prioritize: Distance / Insurance / 24-7 availability") (13d).
- Hospital card: specialties, beds, 24/7 flag, accreditation badge (NABH/JCI), insurance accepted, year established. **No star rating** — this absence is intentional, don't let a teammate "improve" it back in.
- Call + Directions buttons only. No booking button.

### 8. Doctor prescription capture
- Voice-first: mic button, live transcript, fields populate as structured (medicine / dosage / days / timing / food-relation / diagnosis).
- OCR fallback: photo upload → parsed fields → doctor confirms/edits before save (never auto-submits OCR output).
- Diagnosis field is doctor-entered here — same flow, no separate "AI suggests diagnosis" anywhere near this page.

### 9. Doctor summary card
- Read-only for the doctor viewing it: prior meds, dates, prescribing context, prior diagnosis-as-recorded.
- **Must reflect current consent scope** — if patient set "meds only," this page shows meds and hides diagnosis, not just a UI toggle but an actual gated query.

## Design constraints worth stating to your frontend teammate up front
- Voice-first means the mic control needs to be the visually dominant input on capture/discovery pages, not a small icon next to a text box.
- This is a live judged demo: every screen needs a state that looks good with realistic-but-fake data pre-loaded, since you won't have real Coimbatore patients to click through.
- Mobile-first layout matters even though it's a website — patients in an emergency are on a phone, not a laptop.
