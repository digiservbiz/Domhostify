# Roadmap

Progress and blockers live in [status.md](../status.md). Dates are not committed until dependencies and scope are verified.

## Phase 0 — Foundation
- [x] Confirm product direction and repository access.
- [x] Create PRD, architecture, roadmap, status, testing, security, contribution, and decision-log documents.
- [ ] Finalize MVP acceptance criteria.
- [ ] Record decisions as stack/provider choices are verified.

## Phase 1 — Runnable engineering baseline
- [ ] FastAPI application and health endpoint.
- [ ] Dependency/configuration management and environment example.
- [ ] pytest suite and CI workflow.
- [ ] Local run instructions and error handling.
- [ ] Verify build/tests.

## Phase 2 — Domain and hosting comparison demo
- [x] Domain normalization and input validation.
- [x] Typed availability/result contract with explicit unknown state.
- [x] Registrar offer model with registration and renewal pricing.
- [x] Hosting provider and plan catalog (demo catalog plus persistent verified-plan read endpoint).
- [x] Clearly labelled demo data.
- [x] Search/filter/sort endpoints and committed tests (execution still needs verification).
- [x] First responsive web interface (runtime smoke test still pending).

## Phase 3 — Affiliate-ready integrations
- [ ] Inventory provider APIs and affiliate programs.
- [ ] Verify permissions, regional coverage, price fields, and attribution rules.
- [ ] Provider adapters, timeouts, caching, and failure handling.
- [ ] Safe redirect allowlist and click events.
- [ ] Conversion reconciliation where supported.
- [ ] Disclosure and privacy review.

## Phase 4 — Domain aftermarket
- [ ] Listing schema and search.
- [ ] Listing submission/moderation and ownership verification.
- [ ] Buy Now / Make Offer workflows.
- [ ] Transaction partner evaluation and secure transfer procedures.
- [ ] Auctions after core workflows are tested.

## Phase 5 — Seller dashboard and AI intelligence
- [ ] Portfolio import and ownership checks.
- [ ] Pricing guidance with uncertainty.
- [ ] Buyer matching and seller analytics.
- [ ] AI business-launch assistant.
- [ ] Affiliate-neutral recommendations and sponsorship disclosure.

## Phase 6 — Production readiness
- [ ] Authentication, authorization, abuse prevention, and rate limits.
- [ ] Privacy, consent, terms, disclosures, and marketplace policy review.
- [ ] Backups, monitoring, structured logs, alerts, incident response.
- [ ] Accessibility and performance audit.
- [ ] Staging deployment, end-to-end tests, rollback plan.
- [ ] Production launch checklist.

## Release gates
Do not launch live integrations without verified access/terms. Do not enable payments, escrow, automatic registration, or transfers without separate security and compliance review.
