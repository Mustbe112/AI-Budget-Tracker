"""Run from backend/:  python -m scripts.check_db"""
from sqlalchemy import create_engine, text

from app.core.config import settings


def main() -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            version = conn.execute(text("select version()")).scalar_one()
        print("Connected to database.")
        print(version)
    except Exception as exc:  # noqa: BLE001 - we want a friendly message
        # Print only the first line; never print the full URL (it has the password).
        print("Could not connect to the database.")
        print(str(exc).splitlines()[0])
        raise SystemExit(1)


if __name__ == "__main__":
    main()