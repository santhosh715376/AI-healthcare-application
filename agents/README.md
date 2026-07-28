# Agents (AI & Chatbot)

FastAPI server exposing AI graph agents defined in `api-contract.md`.

## Virtual Environment Setup

```bash
# From agents/ or workspace root
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Install dependencies:
pip install -r requirements.txt
```

## Standalone Execution

```bash
uvicorn server:app --reload
```
Uses `contracts/mock-data/mock_hospitals.json` until `backend-and-mapping` service is live.
