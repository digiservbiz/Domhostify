from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, MarketplaceTransaction, MarketplaceTransactionEvent
from backend.app.transactions import transition_transaction


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return engine, sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _transaction():
    return MarketplaceTransaction(
        listing_id=1,
        buyer_ref="buyer-opaque",
        seller_ref="seller-opaque",
        transaction_type="make_offer",
        amount=Decimal("125.50"),
        currency="EUR",
        status="offer_pending",
    )


def test_transaction_transition_records_append_only_event():
    engine, Session = _session()
    try:
        with Session() as db:
            transaction = _transaction()
            db.add(transaction)
            db.flush()
            event = transition_transaction(
                db,
                transaction=transaction,
                target_status="accepted",
                actor_type="seller",
                actor_ref="seller-opaque",
                note="Offer accepted",
            )
            db.commit()
            assert transaction.status == "accepted"
            assert event.from_status == "offer_pending"
            assert event.to_status == "accepted"
            assert event.event_type == "transaction_accepted"
            stored = db.scalar(
                select(MarketplaceTransactionEvent).where(
                    MarketplaceTransactionEvent.transaction_id == transaction.id
                )
            )
            assert stored is not None
            assert stored.actor_ref == "seller-opaque"
    finally:
        engine.dispose()


def test_transaction_rejects_illegal_state_transition():
    engine, Session = _session()
    try:
        with Session() as db:
            transaction = _transaction()
            db.add(transaction)
            db.flush()
            with pytest.raises(ValueError, match="Invalid transaction transition"):
                transition_transaction(
                    db,
                    transaction=transaction,
                    target_status="completed",
                    actor_type="system",
                )
            assert transaction.status == "offer_pending"
            assert db.scalars(select(MarketplaceTransactionEvent)).all() == []
    finally:
        engine.dispose()


def test_completed_transition_sets_completion_timestamp():
    engine, Session = _session()
    try:
        with Session() as db:
            transaction = _transaction()
            transaction.status = "transfer_pending"
            db.add(transaction)
            db.flush()
            transition_transaction(
                db,
                transaction=transaction,
                target_status="completed",
                actor_type="transfer_provider",
            )
            assert transaction.completed_at is not None
    finally:
        engine.dispose()


def test_transaction_actor_and_note_are_validated():
    engine, Session = _session()
    try:
        with Session() as db:
            transaction = _transaction()
            db.add(transaction)
            db.flush()
            with pytest.raises(ValueError, match="Unsupported transaction event actor"):
                transition_transaction(
                    db,
                    transaction=transaction,
                    target_status="accepted",
                    actor_type="random",
                )
            with pytest.raises(ValueError, match="at most 500"):
                transition_transaction(
                    db,
                    transaction=transaction,
                    target_status="accepted",
                    actor_type="seller",
                    note="x" * 501,
                )
    finally:
        engine.dispose()



@pytest.mark.parametrize(
    ("current", "target", "actor"),
    [
        ("payment_pending", "paid", "buyer"),
        ("payment_pending", "paid", "seller"),
        ("payment_pending", "paid", "admin"),
        ("payment_pending", "paid", "system"),
        ("accepted", "payment_pending", "buyer"),
        ("paid", "refunded", "buyer"),
        ("paid", "refunded", "seller"),
    ],
)
def test_payment_state_changes_require_trusted_actor(current, target, actor):
    engine, Session = _session()
    try:
        with Session() as db:
            transaction = _transaction()
            transaction.status = current
            db.add(transaction)
            db.flush()
            with pytest.raises(ValueError):
                transition_transaction(
                    db,
                    transaction=transaction,
                    target_status=target,
                    actor_type=actor,
                )
            assert transaction.status == current
            assert db.scalars(select(MarketplaceTransactionEvent)).all() == []
    finally:
        engine.dispose()


def test_only_payment_provider_can_mark_transaction_paid():
    engine, Session = _session()
    try:
        with Session() as db:
            transaction = _transaction()
            transaction.status = "payment_pending"
            db.add(transaction)
            db.flush()
            event = transition_transaction(
                db,
                transaction=transaction,
                target_status="paid",
                actor_type="payment_provider",
                actor_ref="provider-event-ref",
            )
            assert transaction.status == "paid"
            assert event.actor_type == "payment_provider"
    finally:
        engine.dispose()
