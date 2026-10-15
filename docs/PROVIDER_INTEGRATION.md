# Provider Integration Guide

## Current state

The application now defines a registrar adapter contract in `backend/app/providers.py` and uses a deliberately limited demo implementation. It does not call any registrar API, and domain availability remains `unknown`.

## Contract

A registrar adapter implements `RegistrarProvider.check_domain(domain)` and returns a `DomainAvailability` containing:

- normalized domain queried
- availability: `available`, `unavailable`, `unknown`, or `error`
- source status and provider key
- checked-at timestamp when the provider actually performed a check
- a user-safe explanation

## Rules before enabling a live provider

1. Verify the provider's official API/feed, access eligibility, affiliate terms, and permitted use of pricing data.
2. Keep credentials in deployment secrets or environment variables; never commit them.
3. Set explicit network timeouts and handle rate limits, errors, and provider outages.
4. Treat timeout, malformed response, missing price, or stale result as unknown/error—not available.
5. Preserve the provider's currency and distinguish registration, renewal, and transfer prices.
6. Add unit tests with mocked provider responses and API tests for success, unavailable, timeout, and malformed responses.
7. Add caching only with a documented freshness limit and provider-specific terms.
8. Do not label an offer as affiliate-enabled until the partnership and tracking URL are approved.
9. Do not expose raw provider error bodies, credentials, or request headers to clients.

## Activation strategy

Use a provider registry and configuration flag to opt in one adapter at a time. Keep the demo adapter as the safe fallback. Live provider activation must be a deliberate deployment configuration, not an implicit behavior triggered by a user query.
