# Kyros Identity & Differentiators

Purpose: make Kyros feel crafted, not templated. This document captures naming, UX, runtime invariants, and operational conventions that give the platform a recognizable signature.

## Identity & Naming
- Packages/services: Atlas (registry), Conductor (orchestrator), Forge (terminal daemon), Console (UI), Dialtone (core).
- Domain language: Runs (not Jobs), Capabilities (not Services), Ledger (event store/provenance).
- Public artifacts use the Kyros prefix where appropriate (e.g., kyrosctl, kyros.manifest.*).

## UX & Design
- Kyros Design Tokens: brand palette, spacing, motion; shipped via `@kyros/ui` as a thin wrapper over Carbon components.
- Console IA uses Kyros terms (Runs, Capabilities, Ledger, Policies) and opinionated empty states.
- Storybook theme demonstrating tokens + accessibility patterns.

## Contracts & Manifest
- Kyros Manifest v0.1 (JSON‑Schema): run types, capability selectors, SLAs, policy hooks.
- Kyros Agent Protocol: versioned headers, capability negotiation, safety level; schemas in `protocol/`.

## Runtime Invariants (our stamp)
- Request triad on every edge: `x-kyros-id`, `traceparent`, `x-kyros-idempotency`.
- Run Ledger: deterministic record including input hash, tool list, model id, signable summary artifact.
- Health endpoints unified: `/kyros/livez`, `/kyros/readyz`, `/kyros/diagz` with shared schema.

## Policy & Safety
- Policy‑as‑code (OPA/Rego) under `policy/`; who can invoke which capability, quotas/tiers.
- Redaction profiles by data class (PII, secrets) enforced at edges and in logs/traces.

## Observability
- One‑trace‑per‑run: Console → Conductor → Agents stitched by stable `run_id`.
- Minimal, structured JSON logs everywhere; OTel resource attrs include `service.name`, `deployment.environment`, and `run_id` where applicable.

## Developer Experience & CLI
- `kyrosctl`: scaffold, validate, plan/apply for manifest/contracts; prints diffs and provenance.
- PR template sections: Context, Invariants touched, Policy impact, Observability notes.

## Quick Wins (initial pass)
- Rebrand package names/endpoints; introduce `@kyros/ui` and tokens.
- Add Manifest schema + examples; Protocol readme.
- Implement request triad middleware across services; emit run provenance payloads.
- Rename Jobs → Runs in API, UI, and docs; regenerate clients.
- Standardize `/kyros/*z` health endpoints.

## Acceptance Criteria
- Unique names appear in code, UI, and docs.
- Manifest + Protocol exist and drive codegen/docs.
- Request triad and health schema enforced across services.
- Storybook reflects Kyros theme; Console uses `@kyros/ui` wrappers.

## Next Steps
- Track renames and token work under collaboration/tasks; gate merges on the acceptance criteria above.
- Add ADRs for Manifest v0.1 and Invariants (request triad, health schema).

