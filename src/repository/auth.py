from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from src.database.db import get_db
from sqlalchemy.orm import Session
from src.database.models import Users
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from src.config.config import settings


class Hash:
    """Utility wrapper

    Provides a clear separation between hashing logic and the rest of the
    application so that the underlying algorithm can be swapped easily in the
    future.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain-text password against a hashed digest.

        Args:
            plain_password (str): Raw password provided by the user.
            hashed_password (str): Digest previously generated with
                `get_password_hash`.

        Returns:
            bool: *True* if the password matches, otherwise *False*.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password using the configured algorithm.

        Args:
            password (str): User's raw password.

        Returns:
            str: Cryptographically secure salted hash.
        """
        return self.pwd_context.hash(password)


async def create_access_token(data: dict, expires_delta: int = 3600):
    """Generate a short-lived JWT access token.

    Args:
        data (dict): Payload to encode inside the token. Must contain a
            ``sub`` claim (subject) to uniquely identify the user.
        expires_delta (int): Time-to-live in seconds. Defaults to *3600* (1 h).

    Returns:
        str: Encoded JSON Web Token string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.HASH_SECRET, algorithm=settings.HASH_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db),
):
    """Decode a bearer token and retrieve the corresponding user.

    The function is designed to be used as a FastAPI dependency for route
    protection.

    Args:
        token (HTTPAuthorizationCredentials): Bearer token extracted by
            :class:`fastapi.security.HTTPBearer`.
        db (Session): Database session dependency.

    Raises:
        HTTPException: ``401`` if the token is invalid or user does not exist.

    Returns:
        Users: The authenticated user model instance.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT
        payload = jwt.decode(
            token.credentials,
            settings.HASH_SECRET,
            algorithms=[settings.HASH_ALGORITHM],
        )
        email = payload["sub"]
        if email is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception

    user: Users | None = db.query(Users).filter(Users.email == email).first()
    if user is None:
        raise credentials_exception
    return user
