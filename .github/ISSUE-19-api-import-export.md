# Issue #19: Import/Export API endpoints

## Description
Implement REST API endpoints for full state import/export.

## Tasks
- [ ] GET /api/export/full-state - Export complete game state
- [ ] POST /api/import/full-state - Import complete game state
- [ ] POST /api/import/production-plan - Import production plan only
- [ ] Validate imported JSON schema

## Acceptance Criteria
- Export includes all state (config, inventory, orders, events)
- Import validates and rejects invalid JSON
- Helpful error messages for bad imports

## Phase
Phase 3 - REST API
