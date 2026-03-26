# Issue #11: Simulation engine (day advancement cycle)

## Description
Implement the core simulation engine that processes a full day cycle.

## Tasks
- [ ] Create advance_day function
- [ ] Sequence: Generate demand -> Process POs -> Process orders -> Log events
- [ ] Enforce daily capacity limits
- [ ] Handle partial PO deliveries
- [ ] Update order statuses based on completion
- [ ] Take daily inventory snapshot
- [ ] Add API endpoint to trigger advance

## Acceptance Criteria
- Clicking "Advance Day" runs complete cycle
- All events happen in correct order
- Capacity limits enforced
- State consistent after each cycle

## Phase
Phase 2 - Core Simulation
