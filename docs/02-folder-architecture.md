# 02 - Folder Architecture

Three isolated root folders (`frontend/`, `backend-and-mapping/`, `agents/`) and a shared contract folder (`contracts/`).

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
│   │   ├── pages/
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
