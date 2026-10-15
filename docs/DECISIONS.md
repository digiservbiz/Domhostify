# Architecture Decision Log

Record important decisions with context, alternatives, and consequences. Do not silently treat proposals as settled decisions.

## ADR-0001 — Start as a modular monolith
- Date: 2026-10-15
- Status: Proposed
- Decision: Start with a single API application and explicit module boundaries.
- Context: The repository is at the beginning and the product spans related workflows.
- Alternatives: Split into separate services immediately.
- Consequence: Faster iteration and simpler deployment; maintain module boundaries so splitting remains possible if justified.

## ADR-0002 — Provider data must carry provenance and freshness
- Date: 2026-10-15
- Status: Accepted as a product rule
- Decision: Provider-sourced results include provider/source, checked-at time, and explicit status; unknown is valid.
- Context: Availability/pricing changes and external providers can fail.
- Consequence: Explicit schemas reduce misleading claims.

## ADR-0003 — Keep live integrations out of the first demo
- Date: 2026-10-15
- Status: Proposed
- Decision: Build comparison contracts with clearly labelled demo data before external integrations.
- Context: Provider access, affiliate approval, and terms must be verified.
- Consequence: API/UI can be tested early without implying live data.
