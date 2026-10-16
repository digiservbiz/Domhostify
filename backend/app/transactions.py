"""Marketplace transaction state-machine primitives.

These helpers do not initiate payment or transfer a domain. Provider integrations,
buyer/seller accounts, and transaction endpoints must be implemented separately.
"""
from sqlalchemy.orm import Session

from backend.app.database import MarketplaceTransaction, MarketplaceTransactionEvent, utc_now


ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "offer_pending": frozenset({"accepted", "rejected", "cancelled"}),
    "buy_now_pending": frozenset({"payment_pending", "cancelled"}),
    "accepted": frozenset({"payment_pending", "cancelled"}),
    "payment_pending": frozenset({"paid", "cancelled", "disputed"}),
    "paid": frozenset({"transfer_pending", "disputed", "refunded"}),
    "transfer_pending": frozenset({"completed", "disputed"}),
    "disputed": frozenset({"completed", "refunded"}),
    "rejected": frozenset(),
    "completed": frozenset(),
    "cancelled": frozenset(),
    "refunded": frozenset(),
}


def transition_transaction(
    db: Session,
    *,
    transaction: MarketplaceTransaction,
    target_status: str,
    actor_type: str,
    actor_ref: str | None = None,
    note: str | None = None,
) -> MarketplaceTransactionEvent:
    """Apply one legal transition and append an audit event; caller commits the session."""
    current = transaction.status
    target = target_status.strip().lower()
    if target not in ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise ValueError(f"Invalid transaction transition: {current} -> {target}")
    if actor_type not in {"buyer", "seller", "admin", "system", "payment_provider", "transfer_provider"}:
        raise ValueError("Unsupported transaction event actor type.")
    # Payment-related state must never be advanced by a browser-facing buyer or seller action.
    if target == "payment_pending" and actor_type not in {"system", "payment_provider"}:
        raise ValueError("Payment initiation requires a trusted system or payment provider actor.")
    if target == "paid" and actor_type != "payment_provider":
        raise ValueError("Only a verified payment provider event may mark a transaction paid.")
    if target == "refunded" and actor_type not in {"admin", "payment_provider"}:
        raise ValueError("Refund transitions require an admin or payment provider actor.")
    if note is not None and len(note) > 500:
        raise ValueError("Transaction event note must be at most 500 characters.")

    transaction.status = target
    transaction.updated_at = utc_now()
    if target == "completed":
        transaction.completed_at = utc_now()

    event = MarketplaceTransactionEvent(
        transaction_id=transaction.id,
        event_type=f"transaction_{target}",
        from_status=current,
        to_status=target,
        actor_type=actor_type,
        actor_ref=actor_ref,
        event_note=note,
    )
    db.add(event)
    return event
