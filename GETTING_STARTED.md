# Agentic Agile-V Implementation - Getting Started

This guide shows you how to use the newly implemented Agentic Agile-V executable engineering control system.

## What Has Been Implemented

Based on the comprehensive blueprint in `IMPLEMENTATION_SUMMARY.md`, we have implemented:

### Phase 1: Unified CLI ✅
Complete command-line interface with all core commands:
- `agilev init` - Initialize repository structure
- `agilev new` - Create new tasks
- `agilev brief` - Validate task briefs
- `agilev classify` - Assign and validate risk levels
- `agilev impact` - Create impact analysis
- `agilev validate` - Run validation checks
- `agilev evidence` - Manage evidence bundles
- `agilev status` - Show current process status
- `agilev handoff` - Create handoff documents
- `agilev lock` - Acquire file locks for multi-agent coordination
- `agilev unlock` - Release file locks

### Phase 2: State Kernel ✅
Persistent event log and state management:
- Event logging with hash chain integrity
- Task state management
- Lock management for multi-agent coordination
- Complete audit trail

### Phase 3: Schemas ✅
JSON schemas for all artifacts:
- Event schema with hash chain support
- Task brief schema with all required fields
- Evidence bundle v2 schema with file hashing and audit trail
- Approval schema for human review records

### Phase 4: Policy-as-Code ✅
Risk policy configuration system:
- Risk classification rules
- Evidence requirements by risk level (L0-L4)
- Gate definitions with fail-closed behavior
- Keyword and path-based risk detection

## Installation

### 1. Clone the repositories

```bash
cd /Users/chris/Dev/agile-v
git clone https://github.com/Agile-V/agentic_agile_v.git
cd agentic_agile_v
```

### 2. Install the package

```bash
# Install in development mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### 3. Verify installation

```bash
agilev --help
```

## Quick Start

### 1. Initialize a repository

```bash
cd your-project
agilev init
```

This creates the `.agentic-agile-v/` directory structure:
```
.agentic-agile-v/
  ├── state/
  │   ├── events.jsonl       # Event log with hash chain
  │   ├── tasks.json         # Task state
  │   └── locks.json         # Active locks
  ├── tasks/                 # Task directories
  ├── policies/              # Risk policies
  ├── schemas/               # JSON schemas
  ├── reports/               # Generated reports
  └── logs/                  # Operation logs
```

### 2. Create a new task

```bash
agilev new --title "Add user authentication" --risk L2
```

This creates:
- `.agentic-agile-v/tasks/AAV-0001/` directory
- `brief.yaml` - Task brief template
- `plan.md` - Implementation plan template
- `impact.md` - Impact analysis template
- `evidence.json` - Evidence bundle

### 3. Complete the task brief

Edit `.agentic-agile-v/tasks/AAV-0001/brief.yaml` and fill in:
- Problem statement
- Intended outcome
- Scope and non-goals
- Requirements (with IDs)
- Constraints
- Acceptance criteria

### 4. Validate the brief

```bash
agilev brief AAV-0001
```

### 5. Check risk classification

```bash
agilev classify AAV-0001
```

This shows:
- Required evidence for your risk level
- Required quality gates
- Whether human approval is needed
- Verification mode required

### 6. Create impact analysis

```bash
agilev impact AAV-0001
```

Complete the generated `impact.md` with:
- Affected requirements
- Affected components
- Affected files
- Interface changes
- Required tests
- Risk implications

### 7. Implement your changes

As you make changes, track them in the evidence bundle:

```bash
# Add changed files to evidence
agilev evidence AAV-0001 --add-file src/auth/login.ts
agilev evidence AAV-0001 --add-file tests/auth/login.test.ts
```

### 8. Validate everything

```bash
agilev validate
```

This checks:
- Event chain integrity
- Task state consistency
- Policy compliance
- Evidence completeness

### 9. Check status

```bash
agilev status
```

Shows:
- Task counts by status and risk level
- Active locks
- Event log size

### 10. Create handoff document

```bash
agilev handoff AAV-0001
```

Generates a rehydration document for the next agent or human.

## Multi-Agent Coordination

### Acquire a lock before making changes

```bash
agilev lock AAV-0001 \
  --actor agent:implementation \
  --files src/auth/login.ts,tests/auth/login.test.ts \
  --intent "Implement login rate limiting" \
  --ttl 2
```

### Release the lock when done

```bash
agilev unlock AAV-0001 --actor agent:implementation
```

### Check for conflicts

```bash
agilev status
```

The system will prevent overlapping work by blocking lock acquisition if files are already locked.

## Risk Levels

### L0: Documentation-only
- Required: Task brief
- Gates: None
- Approval: Not required
- Verification: None

### L1: Low-risk internal change
- Required: Task brief, at least one test or rationale, static analysis
- Gates: evidence_schema
- Approval: Not required
- Verification: Self-check

### L2: Normal product change
- Required: Task brief, impact analysis, unit tests, integration tests, interface contracts, traceability, evidence bundle
- Gates: evidence_schema, test_quality, interface_contracts
- Approval: Recommended
- Verification: Peer-check

### L3: High-impact change
- Required: All L2 requirements plus rollback plan, security review, regression tests, independent verification
- Gates: All L2 gates plus security_check, rollback_path, traceability
- Approval: Required
- Verification: Independent

### L4: Critical/regulated change
- Required: All L3 requirements plus formal validation summary, full traceability, release approval
- Gates: All L3 gates plus independent_verification, compliance_check
- Approval: Required
- Verification: Red-team

## Event Log

Every command creates events in `.agentic-agile-v/state/events.jsonl`. Each event includes:
- Unique event ID
- Timestamp
- Event type
- Actor (who did it)
- Task ID (if applicable)
- Summary
- Artifacts created/modified
- SHA-256 hash
- Hash of previous event (for chain integrity)

View events:
```bash
cat .agentic-agile-v/state/events.jsonl | jq
```

## Evidence Bundle v2

The new evidence bundle format includes:
- Schema version: 2.0.0
- Task ID and risk level
- Requirement IDs addressed
- Changed files with SHA-256 hashes
- Test runs with commands, exit codes, timestamps, and durations
- Gate results with tool versions
- Static analysis results
- Independent verification records
- Human approval records

Example:
```json
{
  "schema_version": "2.0.0",
  "task_id": "AAV-0001",
  "risk_level": "L2",
  "requirements": ["REQ-0001", "REQ-0002"],
  "changed_files": [
    {
      "path": "src/auth/login.ts",
      "sha256": "sha256:abc123...",
      "requirement_ids": ["REQ-0001"],
      "change_type": "modify"
    }
  ],
  "test_runs": [
    {
      "id": "TRUN-001",
      "command": "npm test auth",
      "exit_code": 0,
      "status": "passed",
      "started_at": "2026-06-05T20:00:00Z",
      "duration_seconds": 4.2
    }
  ],
  "gate_results": [
    {
      "gate": "evidence_schema",
      "status": "pass",
      "tool_version": "agilev 0.1.0"
    }
  ]
}
```

## Next Steps

The following phases are planned but not yet implemented:

- **Phase 5**: Impact analysis automation
- **Phase 6**: Independent verification workflows
- **Phase 7**: Complete quality gate library
- **Phase 8**: Metrics and dashboard
- **Phase 9**: GitHub Actions integration
- **Phase 10**: MCP server and framework adapters

## Contributing

To contribute to Agentic Agile-V:

1. Read `AGENTS.md` for repository rules
2. Create a task with `agilev new`
3. Follow the Agile-V process
4. Submit evidence with your PR
5. Pass all quality gates

## Support

For issues or questions:
- GitHub Issues: https://github.com/Agile-V/agentic_agile_v/issues
- Documentation: See the `docs/` directory
- Examples: See `.agentic-agile-v/tasks/` for example task structure

## License

MIT License - See LICENSE file for details
