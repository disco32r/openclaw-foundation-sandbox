# Governance Packet

This directory contains the anti-drift foundation.

Work must flow through:

`intake -> admission -> bounded_task -> proof -> promote_or_reject -> retrospective -> deny_register_update`

The validator in `../tools/validate_governance.py` is the first blocking check. A later implementation may replace or supplement it with OPA/Conftest, but warning-only checks do not count.

## Agent Entry

Agents working on governance, admission, routing, candidates, skills/plugins, dashboards, approvals, or builder flow must start with:

- `governance/AGENTS.md`
- `governance/blueprint.md`
- `governance/phase-gates.json`
- `governance/gate-ledger.json`

Only the `ACTIVE` phase in `gate-ledger.json` is executable unless Ryan explicitly changes direction.

## Files

- `blueprint.md`: canonical implementation blueprint and tipping-point definition.
- `AGENTS.md`: scoped agent entrypoint for this governance packet.
- `phase-gates.json`: machine-readable phase definitions, required artifacts, required checks, completion criteria, and anti-drift requirements.
- `gate-ledger.json`: current phase status; exactly one phase must be `ACTIVE`.
- `operating-method.md`: required lifecycle and agent rules.
- `task-admission.schema.json`: required task intake shape.
- `admission-fixtures/`: good and bad packets used to prove gates.
- `candidate-register.jsonl`: nominated/admitted/rejected tools.
- `deny-register.jsonl`: rejected patterns that must not reappear as fresh ideas.
- `model-routing.md`: hosted-model-only routing policy.
- `skill-plugin-register.jsonl`: admitted skills/plugins. Empty means none admitted.
- `custom-code-decisions.jsonl`: admitted custom code. Empty means no custom code admitted.
- `evidence-contract.md`: what counts as proof.
- `community-evidence-contract.md`: required evidence for candidate nomination and promotion.
- `codex-access-contract.md`: required access pattern for Codex, SSH, `Q:`, Git, and VM source edits.
- `gate-review-contract.md`: required packet format for intelligent gate review.
- `gate-reviews/`: reviewer verdicts and evidence assessments for phase promotion.
- `policy-rules.json`: machine-readable gate rules for the validator.
