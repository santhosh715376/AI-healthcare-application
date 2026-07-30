# Folder Architecture v2 — Three Isolated Parts + Shared Contract

Three root folders, one per person, each independently runnable with mock data.
A fourth folder — `contracts/` — is not owned by any one person. It's written together, on day 1, before implementation starts. This is what makes "merge at the end" safe instead of risky.

```
healthcare-mvp/
│
├── contracts/                         ← WRITE THIS FIRST, TOGETHER, DAY 1
│   ├── api-contract.md                # every endpoint: method, path, request body, response body
│   ├── schemas/
│   │   ├── patient.schema.json
│   │   ├── prescription.schema.json
│   │   ├── hospital.schema.json       # what a hospital card object looks like — mapping person defines this
│   │   ├── consent.schema.json
│   │   └── agent-response.schema.json # what specialty_suggestion / ranking agent returns to frontend
│   └── mock-data/
│       ├── mock_hospitals.json        # mapping person ships this on day 1 so agents/frontend don't wait
│       ├── mock_patient.json
│       └── mock_agent_response.json
│
├── frontend/                           # PERSON A — website look
│   ├── src/
│   │   ├── pages/ ...                  # see doc 03 for page list
│   │   ├── components/
│   │   ├── services/                   # calls contracts/api-contract.md endpoints ONLY
│   │   │                                # points at contracts/mock-data/*.json until backend is live
│   │   └── App.jsx
│   ├── package.json
│   └── README.md                       # "run this standalone with: npm run dev -- --mock"
│
├── backend-and-mapping/                # PERSON B — mapping/data + backend stuff
│   ├── src/
│   │   ├── routes/
│   │   │   ├── patients.js
│   │   │   ├── prescriptions.js
│   │   │   ├── consent.js
│   │   │   ├── adherence.js
│   │   │   ├── emergency.js
│   │   │   └── hospitals.js            # geo query, Haversine — reads coimbatore_hospitals.json
│   │   └── services/geoDistance.js
│   ├── data/
│   │   ├── coimbatore_hospitals.json   # real data — Overpass API / healthsites.io, cross-checked
│   │   ├── overpass_query.txt
│   │   └── boundary/                   # DataMeet ward/district boundary files
│   ├── package.json
│   └── README.md                       # "run standalone with: npm run dev — serves contracts/schemas shape"
│
├── agents/                             # YOU — chatbot + AI agents
│   ├── graphs/
│   │   ├── prescription_parser.py
│   │   ├── specialty_suggestion.py     # takes mock_hospitals.json until backend-and-mapping is live
│   │   ├── hospital_ranking.py
│   │   └── drug_info_rag.py            # stretch
│   ├── tools/
│   ├── state.py
│   ├── server.py                       # FastAPI — exposes graphs at endpoints defined in api-contract.md
│   ├── requirements.txt
│   └── README.md                       # "run standalone with: uvicorn server:app — uses mock hospital data"
│
├── docs/
│   ├── 01-solution-and-features.md
│   ├── 02-folder-architecture.md       # this file
│   ├── 03-website-structure.md
│   └── 04-tech-stack.md
│
└── README.md                           # top-level: who owns what, integration checklist below
```

## Why `contracts/` is the part that makes isolation safe

Each of you can build entirely inside your own folder without waiting on the other two, **because** you all build against the same JSON shapes from day 1:

- **You (agents)** don't need real hospital data to build the ranking agent — you build against `contracts/mock-data/mock_hospitals.json`, which has the exact same field names Person B's real `coimbatore_hospitals.json` will have, because you both agreed on `hospital.schema.json` first.
- **Person A (frontend)** doesn't need your agent running or Person B's backend running — they build every page against `contracts/mock-data/*.json`, so the UI is fully clickable on day 2 even if nothing real is wired up yet.
- **Person B (backend/mapping)** doesn't need to know how your ranking agent reasons internally — they just need to know it takes `hospital.schema.json` objects + a priority-weight param and returns `agent-response.schema.json`.

## What goes in `api-contract.md` (write this together, day 1, ~1 hour, non-negotiable)

For every endpoint, one block like this:

```
POST /api/hospitals/rank
Request:  { hospitals: Hospital[], priorityWeights: {distance, insurance, emergency}, patientLocation: {lat, lng} }
Response: { ranked: [{ hospital: Hospital, reason: string, rank: number }] }
Owner: agents/ (you) — called by backend-and-mapping/hospitals.js, which proxies to frontend
```

Do this for: prescription capture, consent check, hospital list, specialty suggestion, ranking, emergency trigger. Six blocks, not sixty — keep it to the endpoints that actually cross a person-boundary.

## Integration checkpoints — don't actually wait until "the end"

**[Likely]** "Merge at the end" is the phrase to drop from your team's vocabulary this week. Replace it with three checkpoints:
- **End of day 1:** contracts/ finalized and committed. Everyone starts building against mocks.
- **End of day 2:** each person demos their own folder standalone (frontend clickable on mocks, your agents returning correct shapes via `curl` or Postman, Person B's real hospital data loading).
- **Day 3, morning:** first real integration — swap mocks for real calls, one endpoint at a time, not all six at once. Fix what breaks *then*, with a full day of buffer left, not on day 4.

If you hit day 3 morning and the shapes don't match what's in `contracts/schemas/`, that's a contract violation from someone's side, not a mystery bug — easy to find and fix because you have a written spec to check against instead of two people guessing what the other one built.
