# Healthcare Continuity MVP — Project Reference Doc (v2)
**4-Day Hackathon Build | Website MVP**

---

## 1. Problem Statement

Patients in India have no persistent, portable health record. A typical visit: register with name + phone number, see a doctor with no prior context, get a paper prescription, and the trail ends there — no continuity if the patient returns, sees a different doctor, or forgets to take medicine.

A second, related gap surfaces specifically in emergencies away from a patient's regular provider — on a highway, late at night, in an unfamiliar area — where the patient has no way to quickly identify a nearby, credible hospital.

**Why this is real, not assumed:**
- India's national solution (ABDM/ABHA) has created 8.79 crore health IDs but suffers from low real-world usage — 22.2% of integration attempts fail due to patient refusal (privacy/Aadhaar-misuse fear), and small clinics face real friction adopting the standard.
- Commercial players (Practo — $500M valuation, 60% India market share; Zocdoc — $426M raised, already ships an AI phone agent) have saturated booking/scheduling. That is **not** the open wedge.
- The underserved layer: **continuity of record + medication adherence + consent-controlled sharing**, not another booking app.

---

## 2. Format Decisions

| Decision | Choice | Reason |
|---|---|---|
| Timeframe | 4 days | Originally scoped for 36hr, expanded |
| Platform | Website (not native app) | Faster to build, no install friction, all needed features work in-browser |
| Input method | Voice-first (Web Speech API) + OCR fallback | Avoids EMR click-fatigue; OCR handles doctors who still handwrite |
| Escalation logic | Rules-based, not LLM-reasoning | More reliable for a live judged demo |
| Emergency hospital discovery | Location + static verified data only — no symptom-classification, no invented ratings, no in-app booking | Keeps the feature inside what's defensible live; avoids re-opening the symptom-routing liability already cut, and avoids competing with Practo/Zocdoc on booking |

---

## 3. Core Components (Locked)

1. **Prescription capture** — voice/tap structured entry (medicine, dosage, days, timing, food-relation, **condition/diagnosis as recorded by the doctor**) with autocomplete/favorites. Designed to be *faster* than paper, not slower (avoids the documented EHR click-fatigue/burnout trap). The diagnosis field is filled in by the doctor at the time of the visit — same voice/tap flow as everything else — never inferred or generated after the fact.
2. **OCR fallback** — repointed AksharDrishti pipeline, for doctors who don't switch off paper.
3. **Identity layer** — internal patient ID as the permanent primary key. Phone number used only as a revocable *lookup* key — never the permanent identity — because Indian mobile numbers can be deactivated and reassigned to a new subscriber after ~90 days of inactivity (TRAI norms), creating real account-takeover risk if phone number were treated as identity.
4. **Linked dependent profiles** — one phone number (an adult's) can manage multiple patient profiles: self + dependents (children, elderly parents) who don't have their own number.
5. **Profile fields** — name, age, structured accessibility/condition fields (mobility, communication mode, free text — respectful terminology, not outdated labels). Flagged: disability data triggers mandatory verifiable guardian consent under India's DPDP Rules 2025.
6. **Persistent structured record** — timestamped, sourced (voice entry vs. OCR), feeds everything downstream.
7. **Doctor-facing summary card** — factual only: medicines, dosage, dates, prescribing context, **and the diagnosis/condition as recorded by the previous doctor** (a human clinician's own documented judgment, relayed as history — not the agent's inference). **No AI-asserted diagnosis, ever.** Automation-bias research shows AI errors drag clinician diagnostic accuracy down (62.5% → 40% in one study) and cause correct diagnoses to be overturned in up to 7% of cases when AI is wrong — especially dangerous under the time pressure of high-volume Indian OPDs. The agent relays what a doctor already concluded; it never generates or guesses a diagnosis itself.
8. **Patient-facing view** — their own timeline, plain language, no dependency on doctor memory or paper.
9. **Consent model** — scoped **per-appointment**: patient chooses "full history / current meds only / nothing" when booking. Access expires with that booking; doesn't carry over to a different doctor. This gates exactly what the doctor's summary card can show — **"meds only" excludes the diagnosis/condition field**, since a recorded condition is arguably more sensitive than a drug name and shouldn't leak through a narrower consent grant.
10. **Adherence tracking + escalation** — rules-based: miss dose → wait → remind → miss again → SMS to a designated contact. Same pattern reused for missed appointments.
11. **Emergency path (manual trigger)** — patient/family **manually triggered** only. The agent never autonomously decides to act in an emergency — it can only detect-and-escalate-to-a-human (call emergency contact, surface to a real doctor, trigger local EMS).
12. **Delivery layer** — Push API + service worker for reminders (works even with the browser tab closed); Twilio SMS as the fallback/escalation channel since a website has no native push the way an app would.

13. **Emergency hospital-discovery map** — for situations where the patient's regular doctor/hospital is unavailable (away from home, late night, on the road). Two-layer flow, Coimbatore district only for the demo:
    - **Layer 1 — nearest by location:** live-location-based map showing nearby hospitals as data points, using standard geospatial nearest-neighbor (e.g. Haversine distance against a curated hospital dataset). No AI, no ranking judgment — pure proximity.
    - **Layer 2 — browse by specialty:** if the patient isn't looking for "nearest" but "which hospital handles X," they filter/browse a directory by specialty tag (cardiology, orthopedics, nephrology, dermatology, etc.) rather than describing symptoms to a chatbot. This deliberately avoids symptom-to-diagnosis classification — see §4 for why that was cut.
    - **Card data shown per hospital — verified/static facts only:** specialties offered, bed count, 24/7 emergency availability, accreditation (NABH/JCI), insurance/TPA accepted, year established. No invented "success rating" or star score — see §4a rationale below for why this was deliberately excluded even though a competitor UI reference includes it.
    - **Action buttons:** "Call" and "Directions" (route via a maps/directions API using the hospital's lat/long). **No in-app appointment booking** — that would duplicate Practo/Zocdoc's core product, the exact space §5 already identifies as saturated and not the target wedge.

---

## 4. Explicitly Cut or Deferred
*(Worth stating out loud in the pitch — shows scoping discipline, not a gap you missed.)*

- **Symptom-to-hospital-type routing** — cut. Highest liability, lowest differentiation; misrouting a symptom is not a claim you want to defend live. This applies equally to the emergency-map chatbot idea considered during scoping ("tell the bot your symptom, it tells you it's kidney-related") — same rule as component #7's "no AI-asserted diagnosis, ever," just aimed at a scared patient instead of a doctor, arguably higher-stakes since the patient has no clinical training to catch a wrong guess. Replaced with specialty-tag browsing (component #13, Layer 2) — the patient self-selects a known specialty rather than the system inferring one from symptoms.
- **Hospital "success rating" / star score** — cut. No trusted public data source equivalent to openFDA/RxNorm exists for Indian hospital outcome ratings. Publishing an invented or scraped number as a trust signal next to a named hospital is a liability the doc's own drug-info-chatbot rationale (component #15) already argues against by analogy. Accreditation (NABH/JCI) — third-party verified — is used as the trust signal instead.
- **In-app appointment booking** — cut. This is the specific product Practo (60% market share) and Zocdoc (AI phone agent already shipped) already own; building it would contradict the doc's own positioning in §5. "Call" + external directions link substitutes for it.
- **Two-way doctor-agent chat** — cut/minimal. Real-world precedent (Cydoc, a 7-year health AI startup) shut down partly because clinicians treated automated interaction as a threat, not a help.
- **Autonomous emergency action** — reframed, not built. Detect-and-escalate-to-human only.
- **Real cross-hospital / ABDM interoperability** — talking point only ("designed to interoperate with ABDM's consent-manager standard later"), not built. Avoids the two-sided cold-start problem of needing other hospitals on your platform.
- **Own national patient-ID system** — not building. ABHA already exists; rebuilding it would be redundant and would raise "why not just use ABHA" from any informed judge.
- **Real OTP/telecom verification** — mocked for the demo.
- **Doctor real-time-presence toggle, thin booking layer** — secondary/optional, only if core components are finished early.

---

## 4a. Additional Component — Medicine Ordering + Drug-Info Chatbot (lower priority, add if time allows)

14. **OTC medicine ordering** — normal e-commerce-style self-service for non-scheduled/over-the-counter medicines (paracetamol, basic antacids, vitamins, etc.) — legally fine, no prescription required.
15. **Schedule H / H1 / X medicine gating** — these require a prescription by Indian law (Schedule H1 specifically targets antibiotics due to antimicrobial-resistance risk; Schedule X drugs can't even be prescribed via telemedicine). Purchase of these is **gated to what's already in the patient's own captured prescription history** (component #1) — reorder only, never open browse-and-buy. This keeps the feature inside the Drugs and Cosmetics Act / Schedule H framework rather than building an unlicensed online-pharmacy risk.
16. **Drug-info chatbot** — for a drug a doctor prescribed that isn't in the ordering database, the chatbot explains general info (what it's used for) using **retrieved data from openFDA/RxNorm (free, public, no-auth government APIs)**, not free LLM generation — avoids hallucinated drug facts. Matches on generic/active-ingredient name (Indian brand names may differ from US openFDA records). Strict scope: informational only — no dosage recommendations, no interaction-checking claims (same clinical-judgment boundary as the diagnosis rule). Always ends with a "confirm with your doctor/pharmacist" disclaimer.

---

## 5. Competitive Grounding (for pitch context)

| Player | Funding/Scale | What they own | Why it's not your target |
|---|---|---|---|
| Practo | $231M raised, ~$500M valuation | 60% of India's online consult market, doctor SaaS/EMR | Booking + provider SaaS, not adherence/continuity |
| Zocdoc | $426M raised, 4M+ patients/month (US) | AI phone scheduling agent ("Zo") | Scheduling, not longitudinal record continuity |
| ABDM (Govt of India) | National infrastructure, 8.79 crore IDs | Health ID + interoperable record standard | Infrastructure exists, but adoption fails at the last mile (small clinics, patient trust) — that's your actual opening |

Note on component #13: hospital-directory UI patterns closely resemble Practo's existing hospital-listing product (accreditation badges, specialty tags, "Find on X" style CTA). The MVP's version intentionally excludes Practo's proprietary star-rating and booking flow to avoid both a data-provenance problem (unverifiable rating source) and direct feature overlap with a dominant competitor's core product.

---

## 6. Still Open / Needs Your Team's Input

- [ ] Team headcount and role split against the 13 locked components (+ 3 lower-priority ones)
- [ ] Real Twilio account for live SMS demo vs. simulated/logged alert for the pitch
- [ ] Whether to prepare a "smarter agentic escalation" talking point for judges, even though the shipped version is rules-based
- [ ] Hosting choice for HTTPS (needed for Push API) — Vercel/Netlify free tier is sufficient
- [ ] Whether the medicine-ordering + drug-info chatbot (components #14–16) make the cut given remaining time, or get deferred to the pitch's "future roadmap" slide
- [ ] Source and manually curate the Coimbatore hospital dataset (specialties, beds, accreditation, insurance, emergency status) for component #13 — needs to be real, checkable data, not scraped ratings
- [ ] Choice of maps/directions API and geolocation permission flow for component #13

---

## 7. One-Line Pitch Framing

*"India already gave every citizen a health ID — it just never reaches the last mile: the clinic that still hands you a paper slip, or the highway at midnight when you don't know which hospital to trust. We built the layer that captures that moment digitally, keeps it with the patient across visits, helps them find real care when it's needed most, and makes sure they actually take what's prescribed — under their own consent control, every step."*
