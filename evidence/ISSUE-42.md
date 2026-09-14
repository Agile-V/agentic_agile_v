# ISSUE-42 conformance evidence

Task: `tasks/ISSUE-42.md`. Base: `54eaa5451fcbfe9fa1c59355584deddbf7cef342`.
Implementation: local branch `fix/issue-42-runtime-conformance`.

| Check | Executed result (2026-09-14) |
|---|---|
| `python -m pytest tests/test_assurance_command.py -q` | 7 passed |
| `ruff check src/agilev/assurance tests/test_assurance_command.py` | Passed |
| Skills `tests/test_runtime_conformance.py`, source subprocess | 24 passed |
| Non-editable wheel installation, fresh Python 3.12 venv | Built and installed with existing `validate` extra |
| Same conformance tests, installed subprocess outside checkout | 24 passed |

The test corpus is owned by the skills companion branch
`fix/issue-42-admission-trust`. Only normalized statuses/reason-code sets in
that corpus have been compared. The protocol is local-conformance only;
provider fixtures are synthetic, no approval consumption/state mutation or
legacy-hook enforcement is established. The full pre-existing runtime suite
has not been rerun; the new module is an isolated `python -m` entrypoint.

AI influence: OpenCode, model `github-copilot/gpt-6-astra` (declared), filesystem,
shell and GitHub CLI tools. Sources: issue #42, runtime AGENTS.md and CLI/package
layout, skills aggregate contracts and test cases. No secrets, hidden reasoning,
or production credentials recorded. Independent review and publication pending.
