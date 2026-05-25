# Tooling Architecture

This scaffold assumes an agent can read files, edit code, run tests, and update evidence. The agent itself may be local or remote, but the engineering control artifacts should be repository-owned and versioned.

## Recommended components

- `AGENTS.md` for repository instructions
- task briefs in `tasks/`
- evidence bundles in `evidence/`
- PR template with evidence path
- CI evidence validation
- test runner integration
- reviewer checklist
- optional hardware evidence archive

## Agent permission model

Use least privilege:

- read repository context
- edit only scoped files
- run allowed commands
- no secret access by default
- no production access
- no hardware flashing without explicit gate
- no external uploads of proprietary data

## Provider independence

The framework is model-provider agnostic. It works with local LLMs, cloud LLMs, coding agents, and hybrid setups. The important part is not the vendor. The important part is that the repository owns the process artifacts and acceptance evidence.
