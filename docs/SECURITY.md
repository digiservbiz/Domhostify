# Security, Privacy, and Trust

## Engineering baseline
- Store secrets in environment variables or a managed secret store; commit placeholders only.
- Validate API inputs and cap input sizes.
- Use timeouts and rate limits for search and redirect endpoints.
- Allow outbound affiliate destinations only from server-managed provider configuration.
- Never fetch arbitrary user-supplied URLs from the server.
- Avoid logging credentials, tokens, or unnecessary personal/query data.
- Use opaque affiliate click IDs and restrict reporting access.
- Patch dependencies and scan them in CI when configured.
- Require authentication/authorization before seller, admin, or transaction writes go live.
- Back up persistent data and test restoration before production launch.

## Trust and transparency
- Identify affiliate links and sponsored placements clearly.
- Show introductory price, renewal price, billing term, currency, source, and freshness when known.
- Mark unknown or stale provider data.
- Explain recommendation criteria; affiliate payout must not secretly dominate ranking.
- Never represent estimates as verified prices or availability.

## Later legal/compliance review
Before launch, review applicable privacy/cookie rules, affiliate disclosure requirements, consumer pricing rules, terms, seller verification, trademark/abuse reporting, payments/escrow, and data retention in intended markets. This document is engineering guidance, not legal advice.
