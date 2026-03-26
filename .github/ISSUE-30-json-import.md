# Issue #30: JSON import with validation

## Description
Implement full game state import from JSON with schema validation.

## Tasks
- [ ] Create import function for full state
- [ ] Validate JSON schema before importing
- [ ] Handle version compatibility
- [ ] Transaction-based import (rollback on error)
- [ ] API endpoint /api/import/full-state
- [ ] Upload button in dashboard

## Acceptance Criteria
- Invalid JSON rejected with clear error
- All state restored correctly
- No partial imports on failure

## Phase
Phase 5 - Import/Export & Polish
