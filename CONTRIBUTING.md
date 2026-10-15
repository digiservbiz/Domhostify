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
Exact commands will be finalized with the initial backend scaffold. The intended workflow is:
1. Create a Python virtual environment.
2. Install project dependencies.
3. Configure local environment variables using placeholders from .env.example.
4. Run tests.
5. Start the API and verify its health endpoint.
6. Check formatting/linting and CI.

## Change checklist
- [ ] Scope matches the PRD.
- [ ] Validation and failure behavior are defined.
- [ ] Tests added or updated.
- [ ] No secrets or unnecessary personal data added.
- [ ] Documentation and status updated.
- [ ] Tests/build were actually run and results recorded.
