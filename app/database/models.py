"""ORM models. Every money column is NUMERIC(12,2) -> Decimal, never float."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.database.enums import BudgetPeriod, Category

MONEY = Numeric(12, 2)


def _in(column: str, enum_cls: type[StrEnum]) -> str:
    """Build "column IN ('a', 'b', ...)" for a CHECK constraint.
    A NULL value passes a CHECK, so nullable columns need no special case."""
    values = ", ".join(f"'{m.value}'" for m in enum_cls)
    return f"{column} IN ({values})"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    # Emails are lower-cased in the auth service before saving.
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # passive_deletes=True lets the database's ON DELETE CASCADE do the work.
    expenses: Mapped[list[Expense]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    incomes: Mapped[list[Income]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    budgets: Mapped[list[Budget]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    savings_goals: Mapped[list[SavingsGoal]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(MONEY)
    description: Mapped[str | None] = mapped_column(String(500))
    merchant: Mapped[str | None] = mapped_column(String(120))
    expense_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="expenses")

    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint(_in("category", Category), name="category_valid"),
        # Reports and algorithms always filter by user + date (+ category).
        Index("ix_expenses_user_date", "user_id", "expense_date"),
        Index("ix_expenses_user_category_date", "user_id", "category", "expense_date"),
    )


class Income(Base):
    __tablename__ = "income"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount: Mapped[Decimal] = mapped_column(MONEY)
    source: Mapped[str] = mapped_column(String(100))
    income_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="incomes")

    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_income_user_date", "user_id", "income_date"),
    )


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # NULL category = an overall budget across all categories.
    category: Mapped[str | None] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(MONEY)
    period: Mapped[str] = mapped_column(String(10))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)  # NULL = open-ended

    user: Mapped[User] = relationship(back_populates="budgets")

    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint(_in("category", Category), name="category_valid"),
        CheckConstraint(_in("period", BudgetPeriod), name="period_valid"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="date_order"),
    )


class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    goal_name: Mapped[str] = mapped_column(String(100))
    target_amount: Mapped[Decimal] = mapped_column(MONEY)
    current_amount: Mapped[Decimal] = mapped_column(
        MONEY, default=Decimal("0.00"), server_default="0"
    )
    target_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="savings_goals")

    __table_args__ = (
        CheckConstraint("target_amount > 0", name="target_positive"),
        CheckConstraint("current_amount >= 0", name="current_nonnegative"),
    )