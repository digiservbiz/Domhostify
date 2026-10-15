"""Provider contracts and safe demo implementations for domain discovery.

Live registrar integrations must implement this interface and only be enabled after
credentials, provider terms, timeouts, and data freshness behavior are configured.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class DomainAvailability:
    domain: str
    availability: str
    source_status: str
    provider_key: str
    checked_at: str | None
    note: str


class RegistrarProvider(Protocol):
    """Minimal adapter contract for a registrar availability source."""

    provider_key: str

    def check_domain(self, domain: str) -> DomainAvailability:
        """Return an explicit available/unavailable/unknown/error result."""


class DemoRegistrarProvider:
    """Safe fallback: never claims availability and never calls external services."""

    provider_key = "demo"

    def check_domain(self, domain: str) -> DomainAvailability:
        return DomainAvailability(
            domain=domain,
            availability="unknown",
            source_status="demo_only",
            provider_key=self.provider_key,
            checked_at=None,
            note=(
                "Demo response. Availability and pricing have not been checked "
                "with a registrar."
            ),
        )


def utc_now_iso() -> str:
    """Shared UTC timestamp helper for real adapters after successful checks."""
    return datetime.now(timezone.utc).isoformat()
