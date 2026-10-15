# Development Guide

## Working principles
1. Read the PRD, architecture, and current status before changing scope.
2. Prefer small, reviewable changes.
3. Add tests for new behavior and bug fixes.
4. Keep configuration in environment variables; never commit secrets.
5. Update API docs and architecture decisions when contracts change.
6. Update status.md with verified progress, blockers, and next actions.
7. Do not describe untested code as working or deployed code as live unless deployment was verified.

## Local workflow
Use Python 3.11 or newer from the repository root.

1. Create and activate a virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Copy .env.example to .env if needed; use real credentials only in your local environment.
4. Run tests with `python -m pytest -q`.
5. Start the API with `python -m uvicorn backend.app.main:app --reload`.
6. Visit /docs on the local server to inspect API schemas.
7. Check the GitHub Actions workflow after pushing changes.

## Change checklist
- [ ] Scope matches the PRD.
- [ ] Validation and failure behavior are defined.
- [ ] Tests added or updated.
- [ ] No secrets or unnecessary personal data added.
- [ ] Documentation and status updated.
- [ ] Tests/build were actually run and results recorded.
