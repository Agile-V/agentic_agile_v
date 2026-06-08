"""
Enhanced Report and Handoff Generation

Generates comprehensive reports and handoff documents with:
- Risk-level specific templates
- Stakeholder-facing summaries
- Technical deep-dive sections
- Evidence visualizations
- Actionable recommendations
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..task_context import TaskContextResolver
from .event_ledger import EventLedger
from .evidence_adapter import EvidenceAdapter


@dataclass
class HandoffReport:
    """Structured handoff report data."""
    task_id: str
    title: str
    risk_level: str
    
    # Overview
    summary: str
    objectives: list[str]
    acceptance_criteria: list[str]
    
    # Implementation
    files_changed: list[str]
    lines_added: int
    lines_deleted: int
    
    # Evidence
    tests_run: int
    tests_passed: int
    test_failures: list[dict[str, Any]]
    
    checks_run: int
    checks_passed: int
    check_failures: list[dict[str, Any]]
    
    # Agent execution
    sessions: list[dict[str, Any]]
    total_iterations: int
    total_tool_calls: int
    
    # Scope compliance
    scope_violations: list[str]
    dependency_changes: list[str]
    public_api_changes: bool
    
    # Timeline
    events: list[dict[str, Any]]
    
    # Recommendations
    recommendations: list[str]
    residual_risks: list[str]
    
    # Metadata
    generated_at: datetime
    generated_by: str


class ReportGenerator:
    """Generates comprehensive reports and handoff documents."""
    
    def __init__(self, repo_dir: Path, agilev_dir: Path):
        """Initialize generator."""
        self.repo_dir = repo_dir
        self.agilev_dir = agilev_dir
        self.resolver = TaskContextResolver()
    
    def generate_handoff(self, task_id: str) -> HandoffReport:
        """
        Generate handoff report for a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Handoff report data
        """
        # Load task brief
        task_brief = self._load_task_brief(task_id)
        
        # Load evidence
        adapter = EvidenceAdapter()
        evidence = adapter.collect_evidence(task_id)
        
        # Load events
        ledger_file = self.agilev_dir / "openhands" / "events.jsonl"
        ledger = EventLedger(ledger_file)
        events = ledger.export_task_timeline(task_id)
        
        # Extract sessions
        sessions = self._extract_sessions(events)
        
        # Analyze changes
        changed_files = evidence.get('changed_files', [])
        git_stats = self._get_git_stats(task_id)
        
        # Extract test/check results
        verification = evidence.get('verification', {})
        tests = verification.get('test_results', [])
        checks = verification.get('check_results', [])
        
        # Extract scope info
        scope = evidence.get('scope_control', {})
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            task_brief, evidence, tests, checks, scope
        )
        
        # Identify residual risks
        residual_risks = self._identify_residual_risks(
            task_brief, evidence, tests, checks
        )
        
        report = HandoffReport(
            task_id=task_id,
            title=task_brief.get('title', task_id),
            risk_level=task_brief.get('risk_level', 'L1'),
            summary=task_brief.get('summary', ''),
            objectives=task_brief.get('objectives', []),
            acceptance_criteria=task_brief.get('acceptance_criteria', []),
            files_changed=changed_files,
            lines_added=git_stats.get('insertions', 0),
            lines_deleted=git_stats.get('deletions', 0),
            tests_run=len(tests),
            tests_passed=sum(1 for t in tests if t.get('status') == 'passed'),
            test_failures=[t for t in tests if t.get('status') == 'failed'],
            checks_run=len(checks),
            checks_passed=sum(1 for c in checks if c.get('status') == 'passed'),
            check_failures=[c for c in checks if c.get('status') == 'failed'],
            sessions=sessions,
            total_iterations=sum(s.get('iterations', 0) for s in sessions),
            total_tool_calls=sum(s.get('tool_calls', 0) for s in sessions),
            scope_violations=scope.get('violations', []),
            dependency_changes=scope.get('dependency_changes', []),
            public_api_changes=scope.get('public_api_changed', False),
            events=events,
            recommendations=recommendations,
            residual_risks=residual_risks,
            generated_at=datetime.now(),
            generated_by="agilev-cli"
        )
        
        return report
    
    def render_handoff_markdown(self, report: HandoffReport) -> str:
        """
        Render handoff report as Markdown.
        
        Args:
            report: Handoff report data
            
        Returns:
            Markdown string
        """
        # Choose template based on risk level
        if report.risk_level in ['L3', 'L4']:
            return self._render_high_risk_handoff(report)
        else:
            return self._render_standard_handoff(report)
    
    def _render_standard_handoff(self, report: HandoffReport) -> str:
        """Render standard handoff for L0-L2."""
        md = f"""# Handoff Report: {report.task_id}

**Title:** {report.title}  
**Risk Level:** {report.risk_level}  
**Generated:** {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")}

## Summary

{report.summary}

## Implementation Overview

### Changes Made

- **Files changed:** {len(report.files_changed)}
- **Lines added:** {report.lines_added}
- **Lines deleted:** {report.lines_deleted}

<details>
<summary>Changed files ({len(report.files_changed)})</summary>

"""
        
        for file in report.files_changed:
            md += f"- `{file}`\n"
        
        md += "\n</details>\n\n"
        
        # Test results
        md += f"""### Test Results

- **Tests run:** {report.tests_run}
- **Tests passed:** {report.tests_passed} ✅
- **Tests failed:** {len(report.test_failures)} {"❌" if report.test_failures else ""}

"""
        
        if report.test_failures:
            md += "**Failed tests:**\n\n"
            for test in report.test_failures:
                md += f"- `{test.get('name', 'unknown')}`: {test.get('message', 'No message')}\n"
            md += "\n"
        
        # Check results
        md += f"""### Quality Checks

- **Checks run:** {report.checks_run}
- **Checks passed:** {report.checks_passed} ✅
- **Checks failed:** {len(report.check_failures)} {"❌" if report.check_failures else ""}

"""
        
        if report.check_failures:
            md += "**Failed checks:**\n\n"
            for check in report.check_failures:
                md += f"- `{check.get('type', 'unknown')}`: {check.get('message', 'No message')}\n"
            md += "\n"
        
        # Scope compliance
        md += f"""### Scope Compliance

- **Dependency changes:** {len(report.dependency_changes)}
- **Public API changes:** {"Yes ⚠️" if report.public_api_changes else "No"}
- **Scope violations:** {len(report.scope_violations)}

"""
        
        if report.scope_violations:
            md += "**Violations:**\n\n"
            for violation in report.scope_violations:
                md += f"- {violation}\n"
            md += "\n"
        
        if report.dependency_changes:
            md += "**Dependency changes:**\n\n"
            for dep in report.dependency_changes:
                md += f"- {dep}\n"
            md += "\n"
        
        # Agent sessions
        if report.sessions:
            md += f"""### Agent Execution

- **Sessions:** {len(report.sessions)}
- **Total iterations:** {report.total_iterations}
- **Total tool calls:** {report.total_tool_calls}

"""
            
            for i, session in enumerate(report.sessions, 1):
                md += f"""**Session {i}:** `{session['session_id']}`
- Role: {session['role']}
- Status: {session['status']}
- Iterations: {session.get('iterations', 0)}

"""
        
        # Recommendations
        if report.recommendations:
            md += "## Recommendations\n\n"
            for rec in report.recommendations:
                md += f"- {rec}\n"
            md += "\n"
        
        # Residual risks
        if report.residual_risks:
            md += "## Residual Risks\n\n"
            for risk in report.residual_risks:
                md += f"- ⚠️ {risk}\n"
            md += "\n"
        
        # Next steps
        md += """## Next Steps

1. **Review this handoff** - Ensure all changes are understood
2. **Run tests locally** - Verify everything works in your environment
3. **Code review** - Have a peer review the implementation
4. **Deploy to staging** - Test in staging environment
5. **Update documentation** - If needed

"""
        
        # Footer
        md += f"""---

*Generated by Agile-V on {report.generated_at.strftime("%Y-%m-%d at %H:%M:%S")}*
"""
        
        return md
    
    def _render_high_risk_handoff(self, report: HandoffReport) -> str:
        """Render detailed handoff for L3-L4 (high risk)."""
        md = f"""# 🔴 HIGH-RISK Handoff Report: {report.task_id}

**Title:** {report.title}  
**Risk Level:** {report.risk_level} (High Risk)  
**Generated:** {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")}

⚠️ **This is a high-risk change requiring additional review and approval.**

## Executive Summary

{report.summary}

### Objectives

"""
        
        for obj in report.objectives:
            md += f"- {obj}\n"
        
        md += "\n### Acceptance Criteria\n\n"
        
        for criteria in report.acceptance_criteria:
            md += f"- [ ] {criteria}\n"
        
        md += f"""

## Detailed Implementation Analysis

### Code Changes

- **Files changed:** {len(report.files_changed)}
- **Lines added:** {report.lines_added}
- **Lines deleted:** {report.lines_deleted}
- **Net change:** {report.lines_added - report.lines_deleted:+d} lines

#### Modified Files

"""
        
        for file in report.files_changed:
            md += f"- `{file}`\n"
        
        md += f"""

### Testing Evidence

**Summary:**
- Total tests: {report.tests_run}
- Passed: {report.tests_passed} ({100 * report.tests_passed / report.tests_run if report.tests_run > 0 else 0:.1f}%)
- Failed: {len(report.test_failures)}

"""
        
        if report.test_failures:
            md += "#### ❌ Test Failures (BLOCKING)\n\n"
            for test in report.test_failures:
                md += f"""**{test.get('name', 'unknown')}**
- Command: `{test.get('command', 'N/A')}`
- Message: {test.get('message', 'No message')}
- Output:
```
{test.get('output', 'No output')[:500]}
```

"""
        
        md += f"""### Quality Assurance

**Summary:**
- Total checks: {report.checks_run}
- Passed: {report.checks_passed} ({100 * report.checks_passed / report.checks_run if report.checks_run > 0 else 0:.1f}%)
- Failed: {len(report.check_failures)}

"""
        
        if report.check_failures:
            md += "#### ❌ Quality Check Failures\n\n"
            for check in report.check_failures:
                md += f"- **{check.get('type', 'unknown')}**: {check.get('message', 'No message')}\n"
            md += "\n"
        
        md += """### Scope and Impact Analysis

#### Dependency Changes
"""
        
        if report.dependency_changes:
            md += "\n⚠️ **Dependencies were modified:**\n\n"
            for dep in report.dependency_changes:
                md += f"- {dep}\n"
            md += "\n**Impact:** Requires dependency review and security scan.\n\n"
        else:
            md += "\n✅ No dependency changes\n\n"
        
        md += "#### API Changes\n\n"
        
        if report.public_api_changes:
            md += "⚠️ **Public API was modified**\n\n"
            md += "**Impact:** May affect downstream consumers. Requires API compatibility review.\n\n"
        else:
            md += "✅ No public API changes\n\n"
        
        md += "#### Scope Violations\n\n"
        
        if report.scope_violations:
            md += "❌ **Scope violations detected:**\n\n"
            for violation in report.scope_violations:
                md += f"- {violation}\n"
            md += "\n**Impact:** Code touched files outside approved scope. Requires justification.\n\n"
        else:
            md += "✅ No scope violations\n\n"
        
        # Agent execution timeline
        if report.sessions:
            md += f"""### Agent Execution History

**Total sessions:** {len(report.sessions)}  
**Total iterations:** {report.total_iterations}  
**Total tool calls:** {report.total_tool_calls}

#### Session Details

"""
            for i, session in enumerate(report.sessions, 1):
                md += f"""**Session {i}: {session['role']} ({session['status']})**
- Session ID: `{session['session_id']}`
- Iterations: {session.get('iterations', 0)}
- Tool calls: {session.get('tool_calls', 0)}
- Duration: {session.get('duration_seconds', 0):.1f}s

"""
        
        # Event timeline
        if report.events:
            md += "### Event Timeline\n\n"
            for event in report.events[-10:]:  # Last 10 events
                timestamp = datetime.fromisoformat(event['timestamp']).strftime("%H:%M:%S")
                md += f"- **{timestamp}** - {event['event_type']}: {event['summary']}\n"
            md += "\n"
        
        # Risk analysis
        md += "## Risk Analysis\n\n"
        
        if report.residual_risks:
            md += "### Identified Residual Risks\n\n"
            for risk in report.residual_risks:
                md += f"- ⚠️ {risk}\n"
            md += "\n"
        
        md += "### Mitigation Recommendations\n\n"
        
        for rec in report.recommendations:
            md += f"- {rec}\n"
        
        md += f"""

## Approval Checklist

For L{report.risk_level[-1]} changes, the following approvals are required:

- [ ] **Technical review** - Senior engineer has reviewed code
- [ ] **Security review** - Security team has assessed risks
- [ ] **Test coverage** - All tests pass with adequate coverage
- [ ] **Documentation** - Changes are documented
- [ ] **Stakeholder approval** - Product/business stakeholders approve

## Next Steps

1. **Complete approval checklist** - Obtain all required approvals
2. **Address any test failures** - All tests must pass
3. **Fix scope violations** - Justify or remove out-of-scope changes
4. **Deploy to staging** - Thorough staging environment testing
5. **Monitor in production** - Extra monitoring for first 24-48 hours

---

*Generated by Agile-V on {report.generated_at.strftime("%Y-%m-%d at %H:%M:%S")}*

*This is a HIGH-RISK change (L{report.risk_level[-1]}). Exercise extra caution.*
"""
        
        return md
    
    def _load_task_brief(self, task_id: str) -> dict[str, Any]:
        """Load and parse task brief."""
        task_brief_path = self.agilev_dir / "tasks" / task_id / "task_brief.md"
        
        if not task_brief_path.exists():
            return {'title': task_id, 'risk_level': 'L1'}
        
        content = task_brief_path.read_text()
        
        # Parse YAML frontmatter and markdown
        brief = {'title': task_id, 'risk_level': 'L1'}
        
        # Extract title from first heading
        for line in content.split('\n'):
            if line.startswith('# '):
                brief['title'] = line[2:].strip()
                break
        
        return brief
    
    def _get_git_stats(self, task_id: str) -> dict[str, int]:
        """Get git statistics for task changes."""
        # This would use git diff to get real stats
        # Placeholder for now
        return {'insertions': 0, 'deletions': 0}
    
    def _extract_sessions(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract session information from events."""
        sessions = []
        session_map = {}
        
        for event in events:
            if event['event_type'] == 'session_started':
                session_id = event.get('actor_session_id')
                if session_id:
                    session_map[session_id] = {
                        'session_id': session_id,
                        'role': event['details'].get('role', 'unknown'),
                        'status': 'running'
                    }
            
            elif event['event_type'] == 'session_completed':
                session_id = event.get('actor_session_id')
                if session_id and session_id in session_map:
                    details = event.get('details', {})
                    session_map[session_id].update({
                        'status': details.get('status', 'unknown'),
                        'iterations': details.get('iterations', 0),
                        'tool_calls': details.get('tool_calls', 0),
                        'duration_seconds': details.get('duration_seconds', 0)
                    })
                    sessions.append(session_map[session_id])
        
        return sessions
    
    def _generate_recommendations(
        self,
        task_brief: dict[str, Any],
        evidence: dict[str, Any],
        tests: list[dict[str, Any]],
        checks: list[dict[str, Any]],
        scope: dict[str, Any]
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Test failures
        failed_tests = [t for t in tests if t.get('status') == 'failed']
        if failed_tests:
            recommendations.append(
                f"Fix {len(failed_tests)} failing test(s) before deployment"
            )
        
        # Check failures
        failed_checks = [c for c in checks if c.get('status') == 'failed']
        if failed_checks:
            recommendations.append(
                f"Address {len(failed_checks)} quality check failure(s)"
            )
        
        # Dependency changes
        if scope.get('dependency_changes'):
            recommendations.append(
                "Review dependency changes for security vulnerabilities"
            )
        
        # Public API changes
        if scope.get('public_api_changed'):
            recommendations.append(
                "Update API documentation and notify downstream consumers"
            )
        
        # Scope violations
        if scope.get('violations'):
            recommendations.append(
                "Justify scope violations or remove out-of-scope changes"
            )
        
        # High risk
        if task_brief.get('risk_level') in ['L3', 'L4']:
            recommendations.append(
                "Obtain security team approval before deployment"
            )
            recommendations.append(
                "Plan for gradual rollout with monitoring"
            )
        
        return recommendations
    
    def _identify_residual_risks(
        self,
        task_brief: dict[str, Any],
        evidence: dict[str, Any],
        tests: list[dict[str, Any]],
        checks: list[dict[str, Any]]
    ) -> list[str]:
        """Identify residual risks."""
        risks = []
        
        # Missing tests
        if not tests:
            risks.append("No test evidence provided - implementation untested")
        
        # Test failures
        failed_tests = [t for t in tests if t.get('status') == 'failed']
        if failed_tests:
            risks.append(f"{len(failed_tests)} tests failing - functionality may be broken")
        
        # Check failures
        failed_checks = [c for c in checks if c.get('status') == 'failed']
        if failed_checks:
            risks.append(f"{len(failed_checks)} quality checks failing - code quality issues")
        
        # No verification
        verification = evidence.get('verification', {})
        if not verification.get('test_results') and not verification.get('check_results'):
            risks.append("No verification evidence - quality unknown")
        
        return risks


def generate_handoff_report(task_id: str, repo_dir: Path, agilev_dir: Path) -> str:
    """
    Generate handoff report for a task.
    
    Args:
        task_id: Task ID
        repo_dir: Repository directory
        agilev_dir: Agile-V directory
        
    Returns:
        Markdown handoff report
    """
    generator = ReportGenerator(repo_dir, agilev_dir)
    report = generator.generate_handoff(task_id)
    return generator.render_handoff_markdown(report)
