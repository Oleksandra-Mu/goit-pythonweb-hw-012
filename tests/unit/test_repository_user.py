import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.database.models import Users, Role, Base
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    change_confirmed_email,
    update_avatar_url,
    update_user_password,
)

from src.schemas.users import UserModelRegister


@pytest.fixture
def mock_session():
    """Fixture to create a mock SQLAlchemy session."""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def user_repository(mock_session):
    """Fixture to create a mock user repository."""
    return {
        "get_user_by_email": partial(get_user_by_email, db=mock_session),
        "create_user": partial(create_user, db=mock_session),
        "update_token": partial(update_token, db=mock_session),
        "change_confirmed_email": partial(change_confirmed_email, db=mock_session),
        "update_avatar_url": partial(update_avatar_url, db=mock_session),
        "update_user_password": partial(update_user_password, db=mock_session),
    }


@pytest.fixture
def user():
    """Fixture to create a mock user."""
    return Users(
        id=1,
        full_name="testuser",
        email="newemail@example.com",
        password="password",
        confirmed=False,
        avatar=None,
        refresh_token=None,
        roles=Role.user,
    )


@pytest.fixture
def user_admin():
    """Fixture to create a mock admin user."""
    return Users(
        id=2,
        full_name="adminuser",
        password="adminpassword",
        confirmed=True,
        avatar=None,
        refresh_token=None,
        roles=Role.admin,
    )


@pytest.fixture
def user_model():
    """Fixture to create a mock user model."""
    return UserModelRegister(
        email="newuser@example.com",
        password="newpassword",
        full_name="New User",
        roles=Role.user,
    )


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await user_repository["get_user_by_email"](email=user.email)

    assert result == user
    assert user.email == "newemail@example.com"
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session, user_model):

    result = await user_repository["create_user"](body=user_model)

    assert isinstance(result, Users)
    assert result.full_name == "New User"
    assert result.full_name == user_model.full_name
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_token(user_repository, mock_session, user):
    new_token = "new_token"
    # Створюємо AsyncMock для результату execute
    mock_execute_result = AsyncMock()
    mock_execute_result.scalar_one_or_none.return_value = user
    # Правильно встановлюємо return_value для mock_session.execute
    mock_session.execute.return_value = mock_execute_result

    result = await user_repository["update_token"](user=user, refresh_token=new_token)

    assert result is not None
    assert result.refresh_token == new_token
    assert result.refresh_token == "new_token"
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_confirmed_email(user_repository, mock_session, user):
    email = user.email
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    await user_repository["change_confirmed_email"](email=email)

    assert user.confirmed is True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_avatar_url(user_repository, mock_session, user_admin, mocker):
    email = user_admin.email
    new_avatar = "https://example.com/avatar.png"
    mock_redis = mocker.AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user_admin
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository["update_avatar_url"](
        email=email, url=new_avatar, redis_client=mock_redis
    )

    assert result is not None
    assert result.avatar == new_avatar
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)
    mock_redis.delete.assert_awaited_once_with(f"user:{email}")


@pytest.mark.asyncio
async def test_update_user_password(user_repository, mock_session, user):
    email = user.email
    new_password = "new_secure_password"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository["update_user_password"](
        email=email, new_password=new_password
    )

    assert result is not None
    assert result.password == new_password

    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_user_password_user_not_found(user_repository, mock_session):
    """Test updating password for a non-existent user raises ValueError."""
    email = "nonexistent@example.com"
    new_password = "new_secure_password"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError) as exc_info:
        await user_repository["update_user_password"](
            email=email, new_password=new_password
        )

    assert str(exc_info.value) == "User not found"
