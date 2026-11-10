from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import Base
from app.database.models import Budget, Expense, Income, User


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _record):  # SQLite ignores FKs unless told to
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def make_user(db: Session, name: str = "somchai") -> User:
    user = User(username=name, email=f"{name}@example.com", password_hash="hashed")
    db.add(user)
    db.commit()
    return user


def test_create_and_read_expense(db):
    user = make_user(db)
    db.add(Expense(user_id=user.id, category="food", amount=Decimal("220.50"),
                   merchant="Som Tam Stall", expense_date=date(2026, 11, 10)))
    db.commit()

    saved = db.scalars(select(Expense)).one()
    assert saved.amount == Decimal("220.50")
    assert saved.user.username == "somchai"
    assert saved.created_at is not None


def test_negative_or_zero_amount_rejected(db):
    user = make_user(db)
    for bad in (Decimal("-1"), Decimal("0")):
        db.add(Expense(user_id=user.id, category="food", amount=bad,
                       expense_date=date(2026, 11, 10)))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_invalid_category_rejected(db):
    user = make_user(db)
    db.add(Expense(user_id=user.id, category="gambling", amount=Decimal("10"),
                   expense_date=date(2026, 11, 10)))
    with pytest.raises(IntegrityError):
        db.commit()


def test_duplicate_email_rejected(db):
    make_user(db, "a")
    db.add(User(username="b", email="a@example.com", password_hash="x"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_budget_end_before_start_rejected(db):
    user = make_user(db)
    db.add(Budget(user_id=user.id, category="food", amount=Decimal("150"),
                  period="daily", start_date=date(2026, 11, 10),
                  end_date=date(2026, 11, 1)))
    with pytest.raises(IntegrityError):
        db.commit()


def test_overall_budget_allows_null_category(db):
    user = make_user(db)
    db.add(Budget(user_id=user.id, category=None, amount=Decimal("15000"),
                  period="monthly", start_date=date(2026, 11, 1)))
    db.commit()
    assert db.scalars(select(Budget)).one().category is None


def test_deleting_user_cascades_to_their_data(db):
    user = make_user(db)
    db.add_all([
        Expense(user_id=user.id, category="food", amount=Decimal("50"),
                expense_date=date(2026, 11, 10)),
        Income(user_id=user.id, amount=Decimal("30000"), source="Salary",
               income_date=date(2026, 11, 1)),
    ])
    db.commit()

    db.delete(user)
    db.commit()

    assert db.scalars(select(Expense)).all() == []
    assert db.scalars(select(Income)).all() == []