# API Contract

Every endpoint definition shared across Frontend, Backend, and Agents.

## Endpoints

### 1. Hospital Ranking
- **Endpoint**: `POST /api/hospitals/rank`
- **Request Body**:
  ```json
  {
    "hospitals": [],
    "priorityWeights": { "distance": 0.4, "insurance": 0.3, "emergency": 0.3 },
    "patientLocation": { "lat": 11.0168, "lng": 76.9558 }
  }
  ```
- **Response Body**:
  ```json
  {
    "ranked": [
      { "hospital": {}, "reason": "string", "rank": 1 }
    ]
  }
  ```
- **Owner**: `agents/` — called by `backend-and-mapping/hospitals.js`, which proxies to frontend.

### 2. Specialty Suggestion
- **Endpoint**: `POST /api/agents/suggest-specialty`
- **Request Body**: `{ "symptoms": "string" }`
- **Response Body**: `{ "suggestedSpecialty": "string", "reasoning": "string" }`
- **Owner**: `agents/`

### 3. Prescription Capture
- **Endpoint**: `POST /api/prescriptions/parse`
- **Request Body**: `{ "prescriptionImageBase64": "string" }`
- **Response Body**: `{ "medications": [], "dosage": "string" }`
- **Owner**: `agents/` / `backend-and-mapping/`

### 4. Consent Check
- **Endpoint**: `POST /api/consent/check`
- **Request Body**: `{ "patientId": "string", "providerId": "string" }`
- **Response Body**: `{ "granted": true, "timestamp": "string" }`
- **Owner**: `backend-and-mapping/`

### 5. Hospital List (Geo Query)
- **Endpoint**: `GET /api/hospitals`
- **Query Params**: `lat`, `lng`, `radiusKm`
- **Response Body**: `Hospital[]`
- **Owner**: `backend-and-mapping/`

### 6. Emergency Trigger
- **Endpoint**: `POST /api/emergency/trigger`
- **Request Body**: `{ "patientId": "string", "location": { "lat": 0, "lng": 0 } }`
- **Response Body**: `{ "status": "dispatched", "dispatchId": "string" }`
- **Owner**: `backend-and-mapping/`
