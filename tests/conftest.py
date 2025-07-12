import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import select

from main import app
from src.database.db import Base, get_db
from src.database.models import Users  # ← ваша модель
from src.services.auth import auth_service  # JWT helper
from src.repository.auth import Hash
from src.routes import users as users_routes

# -------------------- SQLAlchemy engine / session --------------------
TEST_DB_URL = (
    "postgresql+asyncpg://postgres:contactpassword2024@localhost:5432/test_contacts_db"
)
engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# -------------------- Тестовий користувач --------------------
test_user = {
    "full_name": "tester",
    "email": "tester@example.com",
    "password": "12345678",
    "roles": "user",
}


# -------------------- Підготувати БД один раз --------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        pw_hash = Hash().get_password_hash(test_user["password"])
        session.add(
            Users(
                full_name=test_user["full_name"],
                email=test_user["email"],
                password=pw_hash,
                confirmed=True,
            )
        )
        await session.commit()


# -------------------- session fixture --------------------
@pytest_asyncio.fixture
async def async_session():
    async with TestingSessionLocal() as session:
        yield session


# -------------------- dependency overrides --------------------
@pytest.fixture(scope="session")
def client():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    from src.schemas.users import ResponseUser

    async def override_get_current_user():
        return ResponseUser(
            id=1,
            email=test_user["email"],
            full_name=test_user["full_name"],
            avatar=None,
        )

    # вимкнути лімітер SlowAPI
    users_routes.limiter.limit = lambda *a, **k: (lambda f: f)
    try:
        from slowapi.middleware import SlowAPIMiddleware

        app.user_middleware = [
            m for m in app.user_middleware if m.cls is not SlowAPIMiddleware
        ]
        app.middleware_stack = app.build_middleware_stack()
    except ImportError:
        pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[auth_service.get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# -------------------- JWT токен --------------------
@pytest.fixture
async def get_token():
    # встановлюємо тестовий секрет, щоб збігався у всіх місцях
    from src.config.config import settings

    settings.HASH_SECRET = "test_secret"
    return await auth_service.create_access_token(data={"sub": test_user["email"]})


# -------------------- async httpx client (якщо знадобиться) --------------------
from httpx import ASGITransport


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
