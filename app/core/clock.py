"""'Today' in the user's timezone, as an injectable dependency.

Servers usually run in UTC, so date.today() could be yesterday in Bangkok.
Tests override get_today to freeze the date."""
from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends

from app.core.config import settings


def today_local() -> date:
    return datetime.now(ZoneInfo(settings.app_timezone)).date()


def get_today() -> date:
    return today_local()


Today = Annotated[date, Depends(get_today)]