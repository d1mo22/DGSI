# Issue #15: Manufacturing Order API endpoints

## Description
Implement REST API endpoints for manufacturing orders.

## Tasks
- [ ] GET /api/orders - List all manufacturing orders
- [ ] GET /api/orders/pending - List pending orders only
- [ ] GET /api/orders/{order_id} - Get order details with BOM
- [ ] POST /api/orders - Create manual order
- [ ] POST /api/orders/{order_id}/release - Release order to production
- [ ] POST /api/orders/{order_id}/cancel - Cancel order

## Acceptance Criteria
- BOM breakdown included in order details
- Missing materials indicated clearly
- Can_only release if materials available

## Phase
Phase 3 - REST API
