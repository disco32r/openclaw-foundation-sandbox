# Community Evidence Contract

Community evidence is required before adopting or promoting a foundation component, builder tool, dashboard surface, integration, workflow pack, or proof harness.

## Required Fields

Each nominated candidate must have a `candidate-register.jsonl` row with stable id, name, source URL, role, status, evidence grade, numeric score, verdict, pinned source commit or version, and re-review condition.

## Acceptable Evidence

- Maintained source repository with relevant commits, releases, issues, examples, or docs.
- Demonstrated deployment, template, or example that matches the intended use.
- User reports or community reports that describe operational behavior, failure modes, or maintenance burden.
- Local sandbox proof: setup, smoke, rollback, security, and cost checks.

## Not Enough

- Hype without operational proof.
- A docs page with no successful deployment or user evidence.
- A tool that requires broad custom control-plane code to fit the system.
- A candidate that passes research but fails local sandbox proof.

## Promotion Rule

Community evidence may get a candidate into sandbox evaluation. It does not promote the candidate to live. Live promotion requires local evidence under the active phase gate.
