# Testing Strategy

## Test layers
- Unit: domain normalization, price formatting, ranking, provider status mapping, redirect allowlist.
- API/integration: validation, schemas, errors, repositories, provider timeout behavior.
- Contract: adapters map external responses into one internal schema.
- End-to-end: search domain, compare offers, filter hosting plans, browse marketplace listings.
- Security: open redirect attempts, malformed domains, oversized inputs, secret leakage, unauthorized writes.
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

## Initial release gate
The API starts from documented instructions, tests pass, invalid input is handled, clean-database migration round-trip succeeds, and health checks return the documented schema. Check CI before claiming a successful build. Current CI result (2026-10-15): migration round-trip passed and 49 tests passed with one warning; live provider and frontend smoke checks remain outstanding.
