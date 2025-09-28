# Model policy
- Default model for all Kilo modes: GLM-4.5 (subscription).
- Escalation to Claude (4.1 Opus or 4 Sonnet) REQUIRES the exact user token: `APPROVE_CLAUDE`.

# Cost & rate policy
- Keep requests bounded; prefer local analysis and Memory Bank context.
- Never request premium models without explicit approval.
