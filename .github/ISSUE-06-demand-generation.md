# Issue #6: Demand generation service

## Description
Implement configurable demand generation for manufacturing orders.

## Tasks
- [ ] Create demand parameters model (mean, variance per product)
- [ ] Implement random demand generation algorithm
- [ ] Support demand for both finished printers and raw materials
- [ ] Add API endpoint to get/update demand parameters
- [ ] Log demand generation events

## Acceptance Criteria
- Demand generated within configured mean/variance range
- Different demand patterns per product model possible
- Events logged to event_log table

## Phase
Phase 2 - Core Simulation
