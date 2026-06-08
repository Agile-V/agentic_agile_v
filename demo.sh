#!/bin/bash
# Agentic Agile-V - Interactive Demo Script
# This script demonstrates the complete workflow

set -e

echo "============================================================"
echo "AGENTIC AGILE-V - INTERACTIVE DEMO"
echo "============================================================"
echo ""

# Create demo project directory
DEMO_DIR="/var/folders/9q/yt6wn1cx29d6xltyl6_3cjbc0000gn/T/opencode/agilev-demo"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"

echo "📁 Created demo directory: $DEMO_DIR"
echo ""

# Step 1: Initialize
echo "============================================================"
echo "STEP 1: Initialize Agentic Agile-V"
echo "============================================================"
echo "Command: agilev init"
echo ""

# We'll simulate this since we can't run the full CLI without pyyaml
# Instead, let's create the structure manually

mkdir -p .agentic-agile-v/{state,tasks,policies,schemas,reports,logs}

# Create initial state files
echo '{"tasks": {}}' > .agentic-agile-v/state/tasks.json
echo '{"locks": []}' > .agentic-agile-v/state/locks.json
touch .agentic-agile-v/state/events.jsonl

echo "✅ Created .agentic-agile-v/ directory structure"
echo "   - state/ (events, tasks, locks)"
echo "   - tasks/ (task directories)"
echo "   - policies/ (risk policies)"
echo "   - schemas/ (JSON schemas)"
echo ""

# Step 2: Create a task
echo "============================================================"
echo "STEP 2: Create a New Task"
echo "============================================================"
echo "Command: agilev new --title 'Add user registration' --risk L2"
echo ""

# Create task directory
TASK_ID="AAV-0001"
TASK_DIR=".agentic-agile-v/tasks/$TASK_ID"
mkdir -p "$TASK_DIR"

# Create task brief
cat > "$TASK_DIR/brief.yaml" <<'EOF'
task_id: AAV-0001
title: Add user registration
problem_statement: New users need to be able to register for an account
intended_outcome: Users can create accounts with email and password

scope:
  - Registration form UI
  - User creation endpoint
  - Email validation
  - Password strength validation
  - Database schema for users table

non_goals:
  - Email verification (separate task)
  - Social login (future feature)

requirements:
  - id: REQ-0001
    description: User can register with email and password
    priority: must
  - id: REQ-0002
    description: Email must be valid format
    priority: must
  - id: REQ-0003
    description: Password must be at least 8 characters
    priority: must
  - id: REQ-0004
    description: Duplicate emails are rejected
    priority: must

constraints:
  - Must use existing authentication library
  - Must comply with GDPR for user data
  - Password must be hashed with bcrypt

acceptance_criteria:
  - All unit tests pass
  - Integration tests cover happy path and error cases
  - Security review completed
  - No SQL injection vulnerabilities
  - Passwords are never logged or stored in plain text

risk_level: L2
affected_components:
  - Frontend registration component
  - Backend user service
  - Database users table

required_evidence:
  - unit_tests
  - integration_tests
  - security_review
  - interface_contracts

human_approval_required: false
created_at: '2026-06-05T21:00:00Z'
created_by: demo-script
EOF

echo "✅ Created task $TASK_ID: Add user registration"
echo "   Brief: $TASK_DIR/brief.yaml"
echo ""

# Create plan
cat > "$TASK_DIR/plan.md" <<'EOF'
# Implementation Plan: AAV-0001

## Task Summary
Add user registration feature to allow new users to create accounts

## Implementation Approach

### 1. Database Schema (1 hour)
- Create `users` table migration
- Columns: id, email, password_hash, created_at, updated_at
- Add unique constraint on email

### 2. Backend API (2 hours)
- POST /api/users/register endpoint
- Email validation
- Password strength validation
- Bcrypt password hashing
- Duplicate email check

### 3. Frontend Component (2 hours)
- Registration form component
- Form validation
- Error handling
- Success redirect

### 4. Tests (2 hours)
- Unit tests for validation functions
- Unit tests for user service
- Integration tests for registration flow
- Security tests for SQL injection
- Tests for duplicate email handling

## Files to Change

### New Files
- `db/migrations/001_create_users_table.sql`
- `src/api/users/register.ts`
- `src/components/RegistrationForm.tsx`
- `tests/api/users/register.test.ts`
- `tests/components/RegistrationForm.test.tsx`

### Modified Files
- `src/api/routes.ts` (add registration route)
- `src/database/schema.ts` (add users type)

## Tests to Add

### Unit Tests
- Email validation function
- Password strength validation
- User creation service
- Registration form component

### Integration Tests
- Complete registration flow
- Duplicate email rejection
- Invalid email format rejection
- Weak password rejection

## Evidence to Collect

- [ ] Unit test results
- [ ] Integration test results
- [ ] Security scan results (SQL injection, XSS)
- [ ] Code coverage report (>80%)
- [ ] Manual security review notes

## Rollback Strategy

If registration feature causes issues:
1. Disable registration endpoint via feature flag
2. Roll back database migration if needed
3. Remove registration link from UI

## Known Risks

- Database migration may fail on production
- Bcrypt hashing may be slower than expected under load

## Open Questions

- Should we add CAPTCHA for bot prevention?
- What's the password reset strategy? (separate task)
- Do we need rate limiting on registration endpoint?
EOF

echo "✅ Created implementation plan: $TASK_DIR/plan.md"
echo ""

# Create impact analysis
cat > "$TASK_DIR/impact.md" <<'EOF'
# Impact Analysis: AAV-0001

## Summary

Adding user registration feature affects frontend, backend, and database layers.
Low to medium impact - standard CRUD operation with authentication concerns.

## Affected Requirements

- REQ-0001: User can register with email and password
- REQ-0002: Email must be valid format
- REQ-0003: Password must be at least 8 characters
- REQ-0004: Duplicate emails are rejected

## Affected Components

### Frontend
- New RegistrationForm component
- Navigation (add link to registration)

### Backend
- New /api/users/register endpoint
- User service (create user logic)
- Database connection (new queries)

### Database
- New users table
- Email uniqueness constraint

## Affected Files

### New Files (5)
- `db/migrations/001_create_users_table.sql`
- `src/api/users/register.ts`
- `src/components/RegistrationForm.tsx`
- `tests/api/users/register.test.ts`
- `tests/components/RegistrationForm.test.tsx`

### Modified Files (2)
- `src/api/routes.ts` - Add registration route
- `src/database/schema.ts` - Add users type

## Affected Interfaces

### New API Endpoint
```
POST /api/users/register
Request: { email: string, password: string }
Response: { userId: string, token: string }
```

### Database Schema
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## Affected Tests

### New Tests Required
- Email validation (unit)
- Password validation (unit)
- User creation (unit)
- Registration endpoint (integration)
- Duplicate email (integration)
- Invalid input handling (integration)
- Security tests (SQL injection, XSS)

### Existing Tests to Update
- None (new feature)

## Required Regression Tests

- Ensure existing login still works
- Ensure database migrations run cleanly

## Risk Implications

### Security Risks (Medium)
- Password storage must be secure (bcrypt)
- SQL injection vulnerability if not using parameterized queries
- Email validation must prevent malicious input

**Mitigation:**
- Use proven authentication library
- Use ORM with parameterized queries
- Implement input sanitization
- Security code review required

### Performance Risks (Low)
- Bcrypt hashing is CPU-intensive
- Database writes may slow under high load

**Mitigation:**
- Bcrypt work factor tuned for acceptable latency
- Database properly indexed
- Rate limiting on registration endpoint

### Data Risks (Medium - GDPR)
- User data must comply with GDPR
- Passwords must never be logged

**Mitigation:**
- Privacy review
- Logging configured to exclude sensitive data
- Implement right to deletion

## Required Evidence

- [x] Unit test results (all passing)
- [x] Integration test results (all passing)
- [x] Security scan (no high/critical issues)
- [x] Code coverage >80%
- [ ] Security code review completed
- [ ] Privacy review for GDPR compliance

## Open Questions

1. Do we need email verification before account activation?
   - **Decision:** Separate task (AAV-0002)

2. Should we implement rate limiting now or later?
   - **Decision:** Add to backlog, not blocking for MVP

3. What's the password policy beyond 8 characters?
   - **Decision:** Require one uppercase, one number, one special char
EOF

echo "✅ Created impact analysis: $TASK_DIR/impact.md"
echo ""

# Create evidence bundle
cat > "$TASK_DIR/evidence.json" <<'EOF'
{
  "schema_version": "2.0.0",
  "task_id": "AAV-0001",
  "risk_level": "L2",
  "requirements": [
    "REQ-0001",
    "REQ-0002",
    "REQ-0003",
    "REQ-0004"
  ],
  "changed_files": [
    {
      "path": "db/migrations/001_create_users_table.sql",
      "sha256": "sha256:abc123def456...",
      "requirement_ids": ["REQ-0001", "REQ-0004"],
      "change_type": "add"
    },
    {
      "path": "src/api/users/register.ts",
      "sha256": "sha256:def456ghi789...",
      "requirement_ids": ["REQ-0001", "REQ-0002", "REQ-0003", "REQ-0004"],
      "change_type": "add"
    },
    {
      "path": "src/components/RegistrationForm.tsx",
      "sha256": "sha256:ghi789jkl012...",
      "requirement_ids": ["REQ-0001", "REQ-0002", "REQ-0003"],
      "change_type": "add"
    }
  ],
  "test_runs": [
    {
      "id": "TRUN-001",
      "command": "npm test -- users/register.test.ts",
      "exit_code": 0,
      "status": "passed",
      "started_at": "2026-06-05T21:30:00Z",
      "duration_seconds": 2.4,
      "artifact": "test-results/unit-users.xml",
      "artifact_sha256": "sha256:xyz789..."
    },
    {
      "id": "TRUN-002",
      "command": "npm test -- components/RegistrationForm.test.tsx",
      "exit_code": 0,
      "status": "passed",
      "started_at": "2026-06-05T21:32:00Z",
      "duration_seconds": 1.8,
      "artifact": "test-results/unit-components.xml",
      "artifact_sha256": "sha256:stu901..."
    },
    {
      "id": "TRUN-003",
      "command": "npm run test:integration -- registration",
      "exit_code": 0,
      "status": "passed",
      "started_at": "2026-06-05T21:34:00Z",
      "duration_seconds": 5.2,
      "artifact": "test-results/integration.xml",
      "artifact_sha256": "sha256:vwx234..."
    }
  ],
  "gate_results": [
    {
      "gate": "evidence_schema",
      "status": "pass",
      "tool_version": "agilev 0.1.0",
      "details": "Evidence bundle validates against schema v2.0.0"
    },
    {
      "gate": "test_quality",
      "status": "pass",
      "tool_version": "jest 29.0.0",
      "details": "All tests passing, coverage 87%"
    },
    {
      "gate": "interface_contracts",
      "status": "pass",
      "tool_version": "typescript 5.0.0",
      "details": "No breaking changes detected"
    }
  ],
  "static_analysis": [
    {
      "tool": "eslint",
      "status": "passed",
      "path": "reports/eslint.json",
      "hash": "sha256:yza567..."
    },
    {
      "tool": "security-scan",
      "status": "passed",
      "path": "reports/security.json",
      "hash": "sha256:bcd890..."
    }
  ],
  "verification": {
    "mode": "peer-check",
    "status": "passed",
    "verifier": "agent:code-reviewer",
    "path": ".agentic-agile-v/tasks/AAV-0001/verification.md"
  },
  "approval": {
    "required": false,
    "status": "approved",
    "approver": "auto-approved-L2"
  },
  "created_at": "2026-06-05T21:00:00Z",
  "created_by": "agent:implementation"
}
EOF

echo "✅ Created evidence bundle: $TASK_DIR/evidence.json"
echo ""

# Show directory structure
echo "============================================================"
echo "DEMO COMPLETE - Directory Structure"
echo "============================================================"
echo ""
echo "Your demo project now has:"
echo ""

tree -L 3 .agentic-agile-v 2>/dev/null || find .agentic-agile-v -type f -o -type d | grep -v "^.agentic-agile-v$" | sed 's|[^/]*/|  |g'

echo ""
echo "============================================================"
echo "NEXT STEPS"
echo "============================================================"
echo ""
echo "You can explore the created files:"
echo ""
echo "  Task Brief:"
echo "    cat $TASK_DIR/brief.yaml"
echo ""
echo "  Implementation Plan:"
echo "    cat $TASK_DIR/plan.md"
echo ""
echo "  Impact Analysis:"
echo "    cat $TASK_DIR/impact.md"
echo ""
echo "  Evidence Bundle:"
echo "    cat $TASK_DIR/evidence.json | jq"
echo ""
echo "============================================================"
echo "KEY CONCEPTS DEMONSTRATED"
echo "============================================================"
echo ""
echo "✅ Task structure with unique ID (AAV-0001)"
echo "✅ Risk classification (L2 - normal product change)"
echo "✅ Requirements with IDs (REQ-0001 through REQ-0004)"
echo "✅ Comprehensive planning (brief, plan, impact analysis)"
echo "✅ Evidence bundle with:"
echo "   - File hashes (SHA-256)"
echo "   - Test runs with commands and results"
echo "   - Gate results"
echo "   - Verification records"
echo ""
echo "🎉 Demo complete!"
