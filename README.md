# Healthcare MVP

Three isolated components with a shared contract for parallel development.

## Project Structure

- `contracts/` - Shared API contract, JSON schemas, and mock data (Day 1 spec).
- `frontend/` - React / Frontend application (Person A).
- `backend-and-mapping/` - Express / Node backend & geospatial data (Person B).
- `agents/` - Python FastAPI server & AI agent graphs (Person C / Agent Developer).
- `docs/` - Project documentation.

## Integration Checkpoints

- **End of Day 1:** `contracts/` finalized and committed. Everyone starts building against mocks.
- **End of Day 2:** Each person demos their folder standalone with mock data.
- **Day 3 (Morning):** First real integration — swap mocks for real calls, one endpoint at a time.
