from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.core.security import hash_password, verify_password
from app.database.models import User
from app.schemas.auth import UserRegister

# Hashing a dummy password when the user doesn't exist keeps login timing
# similar, so attackers can't tell which usernames exist.
_DUMMY_HASH = hash_password("not-a-real-password")


def register_user(db: Session, data: UserRegister) -> User:
    email = data.email.lower()
    taken = db.scalar(
        select(User.id).where(
            or_(func.lower(User.username) == data.username.lower(), User.email == email)
        )
    )
    if taken is not None:
        raise ConflictError("Username or email is already registered")

    user = User(
        username=data.username, email=email, password_hash=hash_password(data.password)
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two simultaneous registrations; DB unique constraint wins
        db.rollback()
        raise ConflictError("Username or email is already registered") from None
    db.refresh(user)
    return user


def authenticate(db: Session, identifier: str, password: str) -> User | None:
    """identifier may be a username or an email."""
    ident = identifier.strip().lower()
    user = db.scalar(
        select(User).where(or_(func.lower(User.username) == ident, User.email == ident))
    )
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None
    return user if verify_password(password, user.password_hash) else None