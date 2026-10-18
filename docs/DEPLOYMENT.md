# Staging Deployment

DomHostify includes a Render Blueprint at `render.yaml` to create a temporary API staging service and PostgreSQL database. This is for runtime verification only, not production.

## Deploy on Render

1. Open the Render dashboard and choose **New → Blueprint**.
2. Connect the GitHub repository `digiservbiz/DomHostify` and select branch `main`.
3. Review the Blueprint resources before applying. The blueprint creates:
   - `domhostify-api-staging` (Python web service, free plan)
   - `domhostify-db-staging` (free PostgreSQL database)
4. Apply the Blueprint and wait until the service is healthy. The first build installs `requirements.txt` and runs `python -m alembic upgrade head`.
5. Copy the service's actual public URL from Render. Do not guess the URL.
6. From a local Python 3.11+ environment with the repository checked out, run:
   ```bash
   DOMHOSTIFY_API_BASE=https://<actual-staging-service-url> python scripts/runtime_smoke.py
   ```
7. Record the real outcome in `status.md`. Do not mark runtime verification complete based only on a successful build or health check.

## Database URL handling

Render PostgreSQL URLs may use either `postgres://` or `postgresql://`. Both the API and Alembic migration configuration normalize these to SQLAlchemy's installed psycopg 3 driver URL (`postgresql+psycopg://`). The `psycopg[binary]` dependency is included in `requirements.txt`. SQLite URLs used in local development and CI remain unchanged.

## Staging safety

- The free PostgreSQL tier has provider-defined limits and may expire; check the current Render dashboard terms before creating resources.
- Do not store production or personal data in this environment.
- The smoke test creates a temporary seller account, listing, and ownership challenge. It withdraws the listing and revokes its session, but does not delete the account or challenge.
- The smoke test does not prove external DNS propagation, admin moderation, browser flows, payments, registrar integration, or domain transfer.
- The blueprint's CORS origins are local-development origins. Add the exact deployed frontend origin before testing a hosted browser UI; never use a wildcard origin with credentials.
- No live payment, registrar, hosting, or transfer provider is configured by this blueprint.
