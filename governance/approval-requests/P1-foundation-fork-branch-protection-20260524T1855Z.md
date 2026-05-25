# Approval Request: P1 Foundation Fork And Branch Protection

## Decision Needed

Approve external GitHub account work needed to complete P1 `foundation-repo`.

## Why This Is Needed

P1 requires a clean fork foundation and branch protection evidence. Current evidence blocks the gate:

- `git remote -v` shows `origin https://github.com/openclaw/openclaw.git`.
- No Ryan-owned fork remote is configured.
- `gh` is not installed on the VM; source-controlled setup uses `tools/setup_p1_github_environment.py` with `GITHUB_TOKEN`.
- `governance/branch-protection-plan.md` is a plan, not proof of configured protection.
- `python3 tools/check_p1_environment.py` fails until the above are resolved.

The gate review packet is:

`governance/gate-reviews/P1-foundation-repo-20260524T1842Z.json`

Current verdict: `blocked`.

## Protected Boundary

This touches an external account and repository settings. Do not execute without Ryan's explicit approval and confirmed GitHub owner/repo target.

## Required Ryan Input

- `GITHUB_TOKEN` able to create/use the fork, push contents, and manage branch protection.

## Proposed Apply

Use the token-driven setup:

```sh
cd /opt/openclaw
GITHUB_TOKEN=<token> python3 tools/setup_p1_github_environment.py
```

The setup script identifies the authenticated GitHub user, creates or uses that user's `openclaw` fork, sets `upstream` and `origin`, pushes the current branch, configures branch protection, and writes:

`governance/evidence/p1-branch-protection.json`

Branch protection config:

- no direct pushes to protected `main`,
- pull request required,
- at least one review required for runtime/model/integration/dashboard/protected-boundary changes,
- validator check required before merge,
- admin bypass disabled for normal work where supported.

If an organization fork is required instead of the authenticated user's fork, create `governance/p1-environment.json` from `governance/p1-environment.example.json` before running the script.

## Proposed Validation

```sh
cd /opt/openclaw
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
cd /opt/openclaw
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
