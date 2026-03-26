# Issue #4: Docker configuration (multi-stage build, volumes)

## Description
Create Docker configuration for easy cross-platform deployment.

## Tasks
- [ ] Create Dockerfile (multi-stage build)
- [ ] Create docker-compose.yml with service definition
- [ ] Create entrypoint.sh script
- [ ] Configure persistent data volume for SQLite database
- [ ] Add environment variable configuration
- [ ] Test container builds and runs on macOS, Linux, Windows

## Acceptance Criteria
- Container builds successfully
- Both FastAPI (port 8000) and Streamlit (port 8501) accessible
- Database persists across container restarts
- Runs on all three platforms

## Phase
Phase 1 - Foundation
