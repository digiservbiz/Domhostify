#!/usr/bin/env python3
"""Exercise DomHostify's live HTTP API without requiring third-party providers.

Usage:
  DOMHOSTIFY_API_BASE=https://your-staging-api.example python scripts/runtime_smoke.py

The script creates a temporary seller and listing. It attempts to withdraw the
listing after checking the ownership-challenge endpoint. It never prints the
session token or password. Run only against a development/staging environment.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


BASE_URL = os.environ.get("DOMHOSTIFY_API_BASE", "http://127.0.0.1:8000").rstrip("/")
PASSWORD = os.environ.get("DOMHOSTIFY_SMOKE_PASSWORD", "Smoke-Test-Password-2026")
EMAIL = os.environ.get("DOMHOSTIFY_SMOKE_EMAIL", f"smoke-{uuid.uuid4().hex[:12]}@example.com")


class SmokeFailure(RuntimeError):
    pass


def request(method: str, path: str, *, token: str | None = None, payload: dict | None = None,
            expected: int = 200) -> dict | list | None:
    headers = {"Accept": "application/json"}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status = response.status
            raw = response.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SmokeFailure(f"{method} {path}: API request failed ({exc}).") from exc

    if status != expected:
        detail = raw.decode("utf-8", errors="replace")[:500]
        raise SmokeFailure(f"{method} {path}: expected HTTP {expected}, got {status}: {detail}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"{method} {path}: expected a JSON response.") from exc


def main() -> int:
    print(f"DomHostify runtime smoke test against {BASE_URL}")
    request("GET", "/health")
    print("PASS health endpoint")
    request("GET", "/ready")
    print("PASS readiness endpoint")

    account = request(
        "POST", "/api/v1/account/register", expected=201,
        payload={"email": EMAIL, "password": PASSWORD, "role": "seller"},
    )
    if not isinstance(account, dict) or not account.get("access_token"):
        raise SmokeFailure("Registration did not return an access token.")
    token = account["access_token"]
    print("PASS seller registration")

    me = request("GET", "/api/v1/account/me", token=token)
    if not isinstance(me, dict) or me.get("role") != "seller" or me.get("email") != EMAIL.lower():
        raise SmokeFailure("The authenticated account identity or role did not match.")
    print("PASS authenticated /me")

    domain = f"smoke-{uuid.uuid4().hex[:10]}.example.com"
    listing = request(
        "POST", "/api/v1/marketplace/seller/listings", token=token, expected=201,
        payload={"domain": domain, "asking_price": 25, "currency": "EUR", "sale_type": "make_offer"},
    )
    if not isinstance(listing, dict) or not listing.get("id"):
        raise SmokeFailure("Seller listing creation did not return a listing ID.")
    listing_id = listing["id"]
    print("PASS seller listing creation")

    listings = request("GET", "/api/v1/marketplace/seller/listings", token=token)
    if not isinstance(listings, list) or not any(item.get("id") == listing_id for item in listings):
        raise SmokeFailure("New listing was not visible in the seller's listing inventory.")
    print("PASS persisted seller listing appears in inventory")

    challenge = request(
        "POST", f"/api/v1/marketplace/seller/listings/{listing_id}/ownership-challenge",
        token=token, expected=201,
    )
    if not isinstance(challenge, dict) or challenge.get("record_type") != "TXT":
        raise SmokeFailure("Ownership challenge did not return a DNS TXT record.")
    print("PASS ownership challenge generation")

    # Withdraw the test listing so it cannot appear as an active listing.
    request("DELETE", f"/api/v1/marketplace/seller/listings/{listing_id}", token=token)
    print("PASS smoke listing withdrawn")

    request("POST", "/api/v1/account/logout", token=token)
    request("GET", "/api/v1/account/me", token=token, expected=401)
    print("PASS logout revokes the session")
    print("SMOKE TEST PASSED")
    print("Note: DNS publication, admin moderation, payments, and domain transfer require separate staging/provider checks.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
