# Issue #8: Order service

## Description
Implement manufacturing order service for managing production orders.

## Tasks
- [ ] Implement order creation
- [ ] Calculate BOM requirements for an order
- [ ] Check material availability against BOM
- [ ] Release order to production (reserves materials)
- [ ] Mark order as waiting_materials if insufficient
- [ ] Process order completion within capacity limits
- [ ] Cancel order (releases reservations)
- [ ] Add API endpoints for all operations

## Acceptance Criteria
- Orders created with correct BOM breakdown
- Can release only if materials available
- Missing materials triggers waiting_materials state
- Daily capacity enforced

## Phase
Phase 2 - Core Simulation
