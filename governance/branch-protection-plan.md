# Branch Protection Plan

The clean foundation fork must prevent direct, unreviewed promotion.

## Required Rules

- No direct push to the protected main branch.
- All changes enter through a branch.
- Required checks must pass before merge:
  - governance validator,
  - test suite or declared no-code proof,
  - security/audit check when runtime or plugin paths change,
  - evidence-path check for any admitted task.
- At least one review is required for runtime, model routing, skills/plugins, integrations, dashboard, or protected-boundary changes.
- Admin bypass is disabled for normal work.

## Promotion Rule

Merge or live promotion is allowed only when:

- the work has an intake packet,
- admission was `admit`, `sandbox`, or `approval_required`,
- the branch links to task/evidence,
- protected-boundary approval packet exists when needed,
- rollback is documented,
- denied patterns are not present.

## Initial Bootstrap Exception

This foundation packet may be applied as the first bootstrap branch. The bootstrap branch still must pass `tools/validate_governance.py` before it can be treated as a foundation baseline.

