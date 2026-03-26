# Issue #3: Authentication system (login, session, JWT)

## Description
Implement a complete authentication system for the simulator.

## Tasks
- [ ] Create password hashing utilities (bcrypt)
- [ ] Create JWT token generation and validation
- [ ] Implement login endpoint with rate limiting
- [ ] Implement logout endpoint
- [ ] Implement current user endpoint
- [ ] Create auth dependency for protected routes
- [ ] Seed default admin user on first run

## Acceptance Criteria
- Users can login with username/password
- Sessions expire after 24 hours
- Protected routes require valid token
- Default admin user created on first run

## Phase
Phase 1 - Foundation
