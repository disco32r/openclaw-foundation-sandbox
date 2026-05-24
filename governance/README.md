# Governance Packet

This directory contains the anti-drift foundation.

Work must flow through:

`intake -> admission -> bounded_task -> proof -> promote_or_reject -> retrospective -> deny_register_update`

The validator in `../tools/validate_governance.py` is the first blocking check. A later implementation may replace or supplement it with OPA/Conftest, but warning-only checks do not count.

## Files

- `operating-method.md`: required lifecycle and agent rules.
- `task-admission.schema.json`: required task intake shape.
- `admission-fixtures/`: good and bad packets used to prove gates.
- `candidate-register.jsonl`: nominated/admitted/rejected tools.
- `deny-register.jsonl`: rejected patterns that must not reappear as fresh ideas.
- `model-routing.md`: hosted-model-only routing policy.
- `skill-plugin-register.jsonl`: admitted skills/plugins. Empty means none admitted.
- `custom-code-decisions.jsonl`: admitted custom code. Empty means no custom code admitted.
- `evidence-contract.md`: what counts as proof.
- `policy-rules.json`: machine-readable gate rules for the validator.

