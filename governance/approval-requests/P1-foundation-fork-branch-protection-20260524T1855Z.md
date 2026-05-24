# Approval Request: P1 Foundation Fork And Branch Protection

## Decision Needed

Approve external GitHub account work needed to complete P1 `foundation-repo`.

## Why This Is Needed

P1 requires a clean fork foundation and branch protection evidence. Current evidence blocks the gate:

- `git remote -v` shows `origin https://github.com/openclaw/openclaw.git`.
- No Ryan-owned fork remote is configured.
- `gh` is not installed on the VM.
- `governance/branch-protection-plan.md` is a plan, not proof of configured protection.
- `python3 tools/check_p1_environment.py` fails until the above are resolved.

The gate review packet is:

`governance/gate-reviews/P1-foundation-repo-20260524T1842Z.json`

Current verdict: `blocked`.

## Protected Boundary

This touches an external account and repository settings. Do not execute without Ryan's explicit approval and confirmed GitHub owner/repo target.

## Required Ryan Inputs

- GitHub owner or organization for the fork.
- Whether Codex may create/configure the fork using GitHub credentials available in this environment, or whether Ryan will create the fork manually.
- Whether branch protection should apply to `main` immediately after fork creation.

## Proposed Apply

Use the chosen Ryan-owned fork target:

```sh
cd /home/openclaw/foundation-source
git remote rename origin upstream
git remote add origin https://github.com/<RYAN_GITHUB_OWNER>/openclaw.git
git push -u origin codex/foundation-governance-bootstrap
```

Configure branch protection on the fork default branch with:

- no direct pushes to protected `main`,
- pull request required,
- at least one review required for runtime/model/integration/dashboard/protected-boundary changes,
- validator check required before merge,
- admin bypass disabled for normal work where supported.

Exact GitHub API or CLI command depends on the available GitHub credential and target owner.

## Proposed Validation

```sh
cd /home/openclaw/foundation-source
git remote -v
git ls-remote --heads origin
python3 tools/validate_governance.py
python3 tools/check_p1_environment.py
```

Additional validation after branch protection is configured:

- capture branch protection API output or GitHub UI screenshot,
- update `governance/gate-reviews/P1-foundation-repo-*.json` with a pass verdict only if fork and protection evidence are present,
- update `governance/gate-ledger.json` to mark P1 `PASS` and P2 `ACTIVE`,
- rerun `python3 tools/validate_governance.py`.

## Proposed Rollback

```sh
cd /home/openclaw/foundation-source
git remote remove origin
git remote rename upstream origin
git remote -v
```

If a fork was created and should be removed, Ryan must approve deletion separately in GitHub because repository deletion is destructive external-account work.

## Risk

- Wrong GitHub owner would put foundation work in the wrong account.
- Missing branch protection would allow unreviewed promotion.
- Creating or deleting repositories is external-account mutation and must not be done without explicit approval.

## Safe Prep Already Completed

- P0 passed with review packet.
- P1 review packet exists and blocks advancement.
- Source repo is clean at the time this packet was written.
- Validator passes structurally.
