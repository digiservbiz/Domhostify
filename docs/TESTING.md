# Testing Strategy

## Test layers
- Unit: domain normalization, price formatting, ranking, provider status mapping, redirect allowlist.
- API/integration: validation, schemas, errors, repositories, provider timeout behavior.
- Contract: adapters map external responses into one internal schema.
- End-to-end: search domain, compare stored registrar offers, filter hosting plans, browse marketplace listings.
- Browser smoke: load the public frontend, search a domain label, compare a full domain against stored offers, load hosting inventory, and load marketplace inventory without exposing private credentials.
- Security: open redirect attempts, malformed domains, oversized inputs, secret leakage, unauthorized writes, payment-state actor authorization, amount/currency validation, and webhook signature verification.
- Operational: health/readiness, startup configuration, migrations, graceful provider failure.

## CI migration round-trip

The GitHub Actions workflow uses a disposable SQLite database and runs `alembic upgrade head`, `alembic downgrade base`, and `alembic upgrade head` before pytest. This verifies that the current migration chain can be applied, reversed, and reapplied on a clean database. It does not replace a staging-database backup/restore rehearsal or production-database verification.

## Rules
- Demo fixtures must be labelled as demo data.
- Tests must not depend on live registrar APIs or affiliate accounts.
- Mock external calls in normal CI.
- Add regression tests for bugs where practical.
- Do not assert that live prices remain constant.
- Do not mark a milestone complete without recording verification.
- Never expose seller, buyer, or admin credentials in browser JavaScript.

## Current verification
- The latest previously verified GitHub Actions run passed the clean migration round-trip and 56 pytest tests with one warning.
- Payment-provider boundary and payment-state actor-guard tests have since been committed; they are pending CI verification.
- Frontend domain offer comparison, hosting loading, and marketplace loading are committed but require a browser/runtime smoke test before being marked verified.
- Live registrar/hosting provider access is not configured; domain availability remains explicitly unknown.

## Initial release gate
The API starts from documented instructions, tests pass, invalid input is handled, clean-database migration round-trip succeeds, and health checks return the documented schema. Check CI before claiming a successful build. Live provider access, browser smoke testing, real multi-user authentication, live payment processing, and domain transfer remain release blockers. The payment module is a disabled integration boundary only.
