# Model Routing Policy

Only hosted models are allowed. Local models are not an option for this foundation.

OpenClaw model config is the visible source of truth. LiteLLM may be used later as a model proxy for budgets and metrics only. OpenRouter may be used only with explicit provider/privacy constraints.

## Task Classes

| Class | Use | Rule |
|---|---|---|
| `T0-local-readonly` | status checks, summaries | economical hosted model, no mutation |
| `T1-research` | web/docs/community evidence | mid-tier hosted model, citations required |
| `T2-coding` | repo work, tests, patches | Codex/OpenAI coding-capable model |
| `T3-architecture` | governance, strategy, design | premium reasoning model, evidence required |
| `T4-sensitive-personal` | finance, medical, identity, home-security | approved direct or verified zero-retention route only |
| `T5-background-batch` | scheduled reports/scans | bounded cheaper hosted model, isolated session |
| `T6-escalation` | failures, contradictions, protected risk | premium model, approval packet or summary only |

## Fallback Rule

Fallback cannot downgrade privacy. If an approved route for protected data fails, the task stops. It does not silently fall back to a broader provider.

## Budget Envelope

Every autonomous run must define:

- `max_usd_per_run`
- `max_tokens_per_run`
- `max_wall_clock_minutes`
- `max_tool_calls`
- `max_subagents`
- `max_retries`
- `allowed_model_classes`
- `approval_required_above_usd`
- `stop_if_no_new_evidence`

