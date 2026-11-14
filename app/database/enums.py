"""Shared enums. The database stores their lowercase string values."""
from enum import StrEnum


class Category(StrEnum):
    FOOD = "food"
    TRANSPORT = "transport"
    SHOPPING = "shopping"
    BILLS = "bills"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    OTHER = "other"


class BudgetPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"