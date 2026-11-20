"""initial schema: users, expenses, income, budgets, savings_goals

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Frozen copies: a migration must not change if app code changes later.
CATEGORIES = ("food", "transport", "shopping", "bills", "health",
              "entertainment", "education", "other")
PERIODS = ("daily", "weekly", "monthly")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("merchant", sa.String(120), nullable=True),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name=op.f("ck_expenses_amount_positive")),
        sa.CheckConstraint(_in("category", CATEGORIES),
                           name=op.f("ck_expenses_category_valid")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                name=op.f("fk_expenses_user_id_users"),
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expenses")),
    )
    op.create_index("ix_expenses_user_date", "expenses", ["user_id", "expense_date"])
    op.create_index("ix_expenses_user_category_date", "expenses",
                    ["user_id", "category", "expense_date"])

    op.create_table(
        "income",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("income_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name=op.f("ck_income_amount_positive")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                name=op.f("fk_income_user_id_users"),
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_income")),
    )
    op.create_index("ix_income_user_date", "income", ["user_id", "income_date"])

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(30), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("period", sa.String(10), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.CheckConstraint("amount > 0", name=op.f("ck_budgets_amount_positive")),
        sa.CheckConstraint(_in("category", CATEGORIES),
                           name=op.f("ck_budgets_category_valid")),
        sa.CheckConstraint(_in("period", PERIODS),
                           name=op.f("ck_budgets_period_valid")),
        sa.CheckConstraint("end_date IS NULL OR end_date >= start_date",
                           name=op.f("ck_budgets_date_order")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                name=op.f("fk_budgets_user_id_users"),
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_budgets")),
    )
    op.create_index(op.f("ix_budgets_user_id"), "budgets", ["user_id"])

    op.create_table(
        "savings_goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("goal_name", sa.String(100), nullable=False),
        sa.Column("target_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("current_amount", sa.Numeric(12, 2),
                  server_default="0", nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("target_amount > 0",
                           name=op.f("ck_savings_goals_target_positive")),
        sa.CheckConstraint("current_amount >= 0",
                           name=op.f("ck_savings_goals_current_nonnegative")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                name=op.f("fk_savings_goals_user_id_users"),
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_savings_goals")),
    )
    op.create_index(op.f("ix_savings_goals_user_id"), "savings_goals", ["user_id"])


def downgrade() -> None:
    op.drop_table("savings_goals")
    op.drop_table("budgets")
    op.drop_table("income")
    op.drop_table("expenses")
    op.drop_table("users")