# Healthcare Continuity MVP — Solution & Features Doc

## The two problems this solves (X and Y)

**X — Continuity of care.** A patient in India has no persistent, portable health record. Each visit starts from zero: name + phone number, no prior context for the doctor, a paper prescription, no adherence follow-up. ABDM/ABHA exists nationally but fails at the last mile — 22.2% of integration attempts fail on patient refusal, and small clinics don't adopt it. This MVP is the last-mile layer: capture the visit digitally, keep it with the patient (not the clinic), and make the record usable by the *next* doctor.

**Y — Emergency care discovery away from a patient's regular provider.** On a highway, at night, in an unfamiliar area, a patient has no fast way to find a nearby, *credible* hospital. This isn't solved by booking apps (Practo, Zocdoc) — that's scheduling, not emergency discovery — so it's the open wedge, not a copy of an incumbent.

Everything else in the doc is infrastructure that makes X and Y actually work end-to-end: identity, consent, adherence, delivery.

---

## Feature list mapped to what it solves

| # | Feature | Solves | AI/Agent? |
|---|---|---|---|
| 1 | Voice/tap prescription capture | X | Yes — voice/NLP → structured fields |
| 2 | OCR fallback (AksharDrishti) | X | Yes — CV pipeline |
| 3 | Internal patient ID (phone = lookup only) | X | No |
| 4 | Linked dependent profiles | X | No |
| 5 | Accessibility/condition profile fields | X | No |
| 6 | Persistent structured record | X | No (data layer) |
| 7 | Doctor-facing summary card (facts + prior diagnosis as recorded, never AI-asserted) | X | No — relay only |
| 8 | Patient-facing timeline | X | No |
| 9 | Per-appointment consent model (full / meds-only / nothing) | X | No |
| 10 | Adherence tracking + rules-based escalation | X | No — rules, not LLM |
| 11 | Manual-trigger emergency escalation | X + Y | No — detect-and-escalate-to-human only |
| 12 | Push/SMS delivery layer | X | No |
| 13a | Hospital locator — nearest by geolocation (Haversine) | Y | No — deliberately not AI |
| 13b | Hospital locator — browse by specialty tag | Y | No |
| 13c | **Specialty-suggestion agent** (free-text symptom → suggested specialty filters, always overridable) | Y | **Yes — this is the AI story for Y** |
| 13d | **Ranking agent** (weighs distance / 24/7 status / insurance / bed count into a one-line-reasoned shortlist, patient-adjustable weighting) | Y | **Yes** |
| 14–16 | OTC ordering, Schedule H/H1/X gated reorder, drug-info chatbot (RAG on openFDA/RxNorm) | Stretch, not X/Y core | Yes — RAG, not generation |

**Your three real agentic components, in order of pitch strength:**
1. Voice/NLP prescription parsing
2. OCR fallback (CV)
3. Specialty-suggestion + ranking agents (13c/13d) — this is what makes Y defensible as "AI where it earns its place," not AI everywhere.

Drug-info RAG chatbot (16) is a fourth if you have time, but it's stretch, not core.

## What's explicitly NOT AI (and why that's a feature, not a gap)
- Hospital nearest-neighbor lookup (13a): pure geospatial query. Adding AI here reopens the exact "invented trust signal" liability you already cut (star ratings, §4a).
- Doctor summary card diagnosis field: relays what a human doctor already wrote. Automation-bias research shows AI-asserted diagnoses drag clinician accuracy down and get correct diagnoses overturned in up to 7% of wrong-AI cases — never worth the risk for a live demo.
- Emergency trigger: detect-and-escalate-to-human, never autonomous action.

**Pitch line:** "We used AI exactly where it adds real value, and we can defend every place we chose not to."

## Must-ship core vs. stretch (say this out loud to your team before day 3)
- **Must-ship:** #1–3, #6–10 (capture, identity, record, summary card, consent, adherence) — this is the differentiated pitch.
- **Should-ship if agents lead is on track:** #13a–13d (hospital discovery + both agents) — this is your Y story and your second AI pillar.
- **Stretch/roadmap-slide only:** #14–16 (medicine ordering, drug-info chatbot).

A smaller set of fully-working features beats a longer list that's half-built on demo day.
