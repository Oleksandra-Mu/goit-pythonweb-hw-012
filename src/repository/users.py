from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis import Redis
from fastapi import HTTPException, status
from src.database.models import Users, Role
from src.schemas.users import UserModel


async def get_user_by_email(email: str, db: AsyncSession):
    """Return a user by email.

    Args:
        email (str): Email address to search for.
        db (AsyncSession): SQLAlchemy session.

    Returns:
        Users | None: Matching user instance or *None*.
    """
    stmt = select(Users).filter_by(email=email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user


async def create_user(body: UserModel, db: AsyncSession):
    """Persist a new user entity.

    Args:
        body (UserModel): Validated Pydantic model with registration data.
        db (AsyncSession): Database session.

    Returns:
        Users: Newly created user instance with id populated.
    """
    user = Users(**body.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_token(user: Users, refresh_token: str, db: AsyncSession):
    """Update a user's refresh token.

    Args:
        user (Users): SQLAlchemy user instance to update.
        refresh_token (str): Newly issued refresh token string.
        db (AsyncSession): Active SQLAlchemy async session.

    Returns:
        Users: Updated user with refreshed token persisted to DB.
    """
    user.refresh_token = refresh_token
    await db.commit()
    return user


async def change_confirmed_email(email: str, db: AsyncSession) -> None:
    """Set the `confirmed` flag to True for the specified user's email.

    Args:
        email (str): Email address to confirm.
        db (AsyncSession): Active SQLAlchemy async session.
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(
    email: str,
    url: str,
    db: AsyncSession,
    redis_client: Redis | None = None,
):
    """Change user's avatar URL (admin-only).

    Args:
        email (str): Email of the user whose avatar will be changed.
        url (str): New avatar URL.
        db (AsyncSession): Active SQLAlchemy async session.
        redis_client (Redis | None): Optional Redis client for cache invalidation.

    Raises:
        PermissionError: If the user does not have admin privileges.

    Returns:
        Users: Updated user instance.
    """



    user = await get_user_by_email(email, db)
    if user.roles != Role.admin:

        raise PermissionError("Недостатньо прав доступу")
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    if redis_client:
        await redis_client.delete(f"user:{email}")
    return user


async def update_user_password(email: str, new_password: str, db: AsyncSession):
    """Replace user's password.

    Note: The *new_password* should be pre-hashed at the service layer.

    Args:
        email (str): Email of the user to update.
        new_password (str): Securely hashed password string.
        db (AsyncSession): Active SQLAlchemy async session.

    Returns:
        Users: User with updated password.

    Raises:
        ValueError: If user is not found.
    """
    user = await get_user_by_email(email, db)
    if user is None:
        raise ValueError("User not found")
    user.password = new_password
    await db.commit()
    await db.refresh(user)
    return user


# async def get_users(db: Session):
#     users = db.query(Users).all()
#     return users

# async def get_user_by_id(user_id: int, db: Session):
#     user = db.query(Users).filter_by(id=user_id).first()
#     return user

# async def update_user(body: UserModel, user_id: int, db: Session):
#     user = db.query(Users).filter_by(id=user_id).first()
#     if user:
#         user.email = body.email
#         db.commit()
#     return user

# async def remove_user(user_id: int, db: Session):
#     user = db.query(Users).filter_by(id=user_id).first()
#     if user:
#         db.delete(user)
#         db.commit()
#     return user
