# Local admission conformance command

Task brief: `tasks/ISSUE-42.md`. Contract owner: `Agile-V/agile_v_skills`.

```bash
python -m pip install -e '.[validate]'
python -m agilev.assurance --manifest
python -m agilev.assurance --trusted-context /trusted/context.json \
  --schemas /trusted/agile_v_skills/schemas < candidate.json
```

Exit 0 means the read-only evaluation admitted the request; exit 1 means
rejection; exit 2 means invalid CLI usage. This command does not execute or
authorize external effects, mutate task state, sign receipts, or consume
single-use approvals. It is not connected to the existing OpenHands hooks.

Candidate JSON contains `gate` and `bundle` envelopes. Trusted JSON separately
contains `decision_context`, `now`, adapter and property profile maps, approval
and exception records, plus `authenticated_approvals`/`authenticated_exceptions`.
Those lists are **synthetic conformance-provider inputs**, not a substitute
for production authentication. Candidate stdin cannot specify the trusted
file or schema root. The caller controls file permissions and trusted paths.

`python -m agilev.assurance --manifest` exports the packaged, versioned
`compatibility.json`. It describes this preview implementation and its limits,
not a released version or proof of conformance in any other deployment.

Cross-repository check, from the skills repository:

```bash
AGILEV_RUNTIME_CHECKOUT=/path/to/agentic_agile_v \
  python -m pytest tests/test_runtime_conformance.py -q
```

The runtime evaluates these cases independently of `contracts.semantics`;
the test driver compares normalized result status and reason-code sets. The
schemas are shared canonical inputs. No production credentials are involved.
