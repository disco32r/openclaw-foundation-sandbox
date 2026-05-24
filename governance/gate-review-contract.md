# Gate Review Contract

The validator is deterministic. It does not decide whether a phase is wise, complete, or safe to promote. That judgment lives in gate review packets.

## Review Packet Location

Gate review packets live under:

`governance/gate-reviews/`

Each packet is JSON and is referenced from `governance/gate-ledger.json` by `review_packet`.

## Required Judgment

A review packet must assess:

- every `completion_criteria` item from the phase definition,
- every `anti_drift_requirements` item from the phase definition,
- mechanical validator output,
- evidence quality,
- runtime enforcement scope,
- blocking findings,
- next action.

## Verdicts

- `pass`: evidence is strong enough to advance the phase.
- `fail`: evidence contradicts completion or drift risk remains unacceptable.
- `blocked`: evidence is missing or the next decision requires Ryan or protected runtime work.

## Promotion Rule

A phase may be marked `PASS` only when the referenced review packet has verdict `pass`, every criterion is `pass`, every anti-drift requirement is `pass`, runtime enforcement is stated, and blocking findings are empty.

For phases with `ryan_required=true`, the ledger must also contain a Ryan approval record before `PASS`.

## Independence Limits

The reviewer must identify whether it is a separate agent, the lead agent in a reviewer role, or a human. If the reviewer is not independent enough for the risk level, the verdict should be `blocked` or `fail`, not `pass`.
